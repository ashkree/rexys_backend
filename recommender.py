from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class BaseRecommender:
    def __init__(self, items):
        self.items = items

    def calculate_cb_score(self, item_index, tfidf_matrix):
        similarities = cosine_similarity(
            tfidf_matrix[item_index], tfidf_matrix).flatten()
        return np.mean(similarities)

    def apply_fuzzy_logic(self, preference_scores, cb_scores, ratings, popularity):
        raise NotImplementedError("Subclasses should implement this method.")

    def recommend(self, user_preferences, user_history):
        raise NotImplementedError("Subclasses should implement this method.")


class MovieRecommender(BaseRecommender):
    def __init__(self, items):
        super().__init__(items)
        self.weights = {
            'genre': 0.27,
            'tags': 0.29,
            'rating': 0.24,
            'actors': 0.20,
        }
        self.fuzzy_system = self._create_fuzzy_system()

    def _create_fuzzy_system(self):
        overall_score = ctrl.Antecedent(
            np.arange(0, 1.1, 0.1), 'overall_score')
        rating = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'rating')
        pop = ctrl.Antecedent(np.arange(0, 1000000, 1000), 'popularity')
        recommendation = ctrl.Consequent(
            np.arange(0, 1.1, 0.1), 'recommendation')

        overall_score['low'] = fuzz.trimf(overall_score.universe, [0, 0, 0.5])
        overall_score['medium'] = fuzz.trimf(
            overall_score.universe, [0.3, 0.5, 0.7])
        overall_score['high'] = fuzz.trimf(overall_score.universe, [0.5, 1, 1])

        rating['poor'] = fuzz.trimf(rating.universe, [0, 0, 4])
        rating['average'] = fuzz.trimf(rating.universe, [3, 5, 7])
        rating['good'] = fuzz.trimf(rating.universe, [6, 10, 10])

        pop['low'] = fuzz.trimf(pop.universe, [0, 0, 300000])
        pop['medium'] = fuzz.trimf(pop.universe, [200000, 500000, 800000])
        pop['high'] = fuzz.trimf(pop.universe, [600000, 1000000, 1000000])

        recommendation['poor'] = fuzz.trimf(
            recommendation.universe, [0, 0, 0.5])
        recommendation['average'] = fuzz.trimf(
            recommendation.universe, [0.3, 0.5, 0.7])
        recommendation['good'] = fuzz.trimf(
            recommendation.universe, [0.5, 1, 1])

        rules = [
            ctrl.Rule(overall_score['high'] & rating['good']
                      & pop['high'], recommendation['good']),
            ctrl.Rule(overall_score['medium'] & rating['average']
                      & pop['medium'], recommendation['average']),
            ctrl.Rule(overall_score['low'] & rating['poor']
                      & pop['low'], recommendation['poor']),
            ctrl.Rule(overall_score['high'] & rating['good']
                      & pop['low'], recommendation['average']),
            ctrl.Rule(overall_score['low'] & rating['good']
                      & pop['high'], recommendation['average'])
        ]

        ranking_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(ranking_ctrl)

    def calculate_preference_score(self, item, user_preferences):
        score = 0

        if 'genre' in user_preferences:
            movie_genres = [g.strip().lower()
                            for g in item['genre'].split(',')]
            if user_preferences['genre'].lower() in movie_genres:
                score += self.weights['genre']

        if 'tags' in user_preferences and 'tags' in item:
            item_tags = [tag.strip().lower() for tag in item['tags']]
            pref_tags = [tag.strip().lower()
                         for tag in user_preferences['tags']]
            matching_tags = set(item_tags).intersection(set(pref_tags))
            score += self.weights['tags'] * \
                len(matching_tags) / len(user_preferences['tags'])

        if 'rating' in user_preferences and 'rating' in item:
            min_rating = user_preferences['rating'].get('min', float('-inf'))
            max_rating = user_preferences['rating'].get('max', float('inf'))
            if min_rating <= item['rating'] <= max_rating:
                score += self.weights['rating']

        if 'actors' in user_preferences and 'actors' in item:
            item_actors = [actor.strip().lower() for actor in item['actors']]
            pref_actors = [actor.strip().lower()
                           for actor in user_preferences['actors']]
            matching_actors = set(item_actors).intersection(set(pref_actors))
            score += self.weights['actors'] * \
                len(matching_actors) / len(user_preferences['actors'])

        return score

    def recommend(self, user_preferences, user_history=None):
        if user_history is None:
            user_history = []

        try:
            print(f"""
                  Starting recommendation process for {len(self.items)} items
                  """)
            print(f"User preferences: {user_preferences}")
            print(f"User history length: {len(user_history)}")

            available_items = [
                item for item in self.items if item not in user_history]
            print(f"""
                  Available items after history filter: {len(available_items)}
                  """)

            if not available_items:
                return []

            tfidf_vectorizer = TfidfVectorizer(
                tokenizer=lambda x: x, preprocessor=lambda x: x)
            item_tags = [item.get('tags', []) for item in available_items]
            print(f"Sample tags: {item_tags[:2]}")

            tfidf_matrix = tfidf_vectorizer.fit_transform(item_tags)
            print("TF-IDF matrix created successfully")

            scores = []
            for idx, item in enumerate(available_items):
                try:
                    print(f"\nProcessing item {idx}: {
                        item.get('title', 'Unknown')}")

                    preference_score = self.calculate_preference_score(
                        item, user_preferences)
                    print(f"Preference score: {preference_score}")

                    cb_score = self.calculate_cb_score(idx, tfidf_matrix)
                    print(f"CB score: {cb_score}")

                    if preference_score > 0 or cb_score > 0:
                        overall_score = 0.7 * preference_score + 0.3 * cb_score
                        print(f"Overall score: {overall_score}")

                        rating = float(item.get('rating', 0))
                        popularity = float(
                            min(item.get('popularity', 0), 1000000))
                        print(f"Rating: {rating}, Popularity: {popularity}")

                        self.fuzzy_system.input['overall_score'] = overall_score
                        self.fuzzy_system.input['rating'] = rating
                        self.fuzzy_system.input['popularity'] = popularity

                        self.fuzzy_system.compute()
                        final_score = float(
                            self.fuzzy_system.output['recommendation'])
                        print(f"Final fuzzy score: {final_score}")

                        scores.append((item, final_score))

                except Exception as e:
                    print(f"Error processing item {idx}: {str(e)}")
                    print(f"Item data: {item}")

            ranked_items = sorted(scores, key=lambda x: x[1], reverse=True)
            print(f"Final number of recommendations: {len(ranked_items[:10])}")
            return ranked_items[:10]

        except Exception as e:
            print(f"Critical error in recommendation process: {str(e)}")
            return []


class GameRecommender(BaseRecommender):
    def __init__(self, items):
        super().__init__(items)
        self.fuzzy_system = self._create_fuzzy_system()

    def _create_fuzzy_system(self):
        rating = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'rating')
        cost = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'cost')
        popularity = ctrl.Antecedent(
            np.arange(0, 15000000, 100000), 'popularity')
        recommendation = ctrl.Consequent(
            np.arange(0, 1.1, 0.1), 'recommendation')

        rating['low'] = fuzz.trimf(rating.universe, [0, 0, 0.7])
        rating['medium'] = fuzz.trimf(rating.universe, [0.6, 0.8, 0.9])
        rating['high'] = fuzz.trimf(rating.universe, [0.8, 0.95, 1])

        cost['cheap'] = fuzz.trimf(cost.universe, [0, 0, 5])
        cost['moderate'] = fuzz.trimf(cost.universe, [4, 7, 10])
        cost['expensive'] = fuzz.trimf(cost.universe, [8, 15, 100])

        popularity['low'] = fuzz.trimf(popularity.universe, [0, 0, 5000000])
        popularity['medium'] = fuzz.trimf(
            popularity.universe, [3000000, 7500000, 12000000])
        popularity['high'] = fuzz.trimf(
            popularity.universe, [10000000, 15000000, 15000000])

        recommendation['poor'] = fuzz.trimf(
            recommendation.universe, [0, 0, 0.5])
        recommendation['good'] = fuzz.trimf(
            recommendation.universe, [0.3, 0.6, 0.8])
        recommendation['excellent'] = fuzz.trimf(
            recommendation.universe, [0.7, 1, 1])

        rules = [
            ctrl.Rule(rating['high'] & cost['cheap'] &
                      popularity['high'], recommendation['excellent']),
            ctrl.Rule(rating['high'] & cost['cheap'] &
                      popularity['medium'], recommendation['excellent']),
            ctrl.Rule(rating['high'] & cost['moderate'] &
                      popularity['high'], recommendation['excellent']),
            ctrl.Rule(rating['high'] & cost['expensive'] &
                      popularity['high'], recommendation['good']),
            ctrl.Rule(rating['medium'] & cost['cheap'] &
                      popularity['high'], recommendation['good']),
            ctrl.Rule(rating['medium'] & cost['moderate'] &
                      popularity['medium'], recommendation['good']),
            ctrl.Rule(rating['medium'] & cost['expensive'] &
                      popularity['low'], recommendation['poor']),
            ctrl.Rule(rating['low'] & cost['cheap'] &
                      popularity['high'], recommendation['good']),
            ctrl.Rule(rating['low'] & cost['moderate'] &
                      popularity['medium'], recommendation['poor']),
            ctrl.Rule(rating['low'] & cost['expensive'] &
                      popularity['low'], recommendation['poor'])
        ]

        ranking_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(ranking_ctrl)

    def recommend(self, user_preferences, user_history=None):
        if user_history is None:
            user_history = []

        available_items = [
            item for item in self.items if item not in user_history]
        if not available_items:
            return []

        # Filter by genre if specified
        if 'genre' in user_preferences:
            available_items = [
                item for item in available_items
                if user_preferences['genre'].lower() in [g.strip().lower() for g in item['genre'].split(',')]
            ]

        # Filter by rating range if specified
        if 'rating' in user_preferences:
            min_rating = user_preferences['rating'].get('min', 0)
            max_rating = user_preferences['rating'].get('max', 10)
            available_items = [
                item for item in available_items
                if min_rating <= item['rating']*10 <= max_rating
            ]

        # Apply fuzzy logic
        fuzzy_scores = []
        for item in available_items:
            try:
                self.fuzzy_system.input['rating'] = float(
                    item.get('rating', 0))
                self.fuzzy_system.input['cost'] = float(item.get('cost', 0))
                self.fuzzy_system.input['popularity'] = float(
                    item.get('popularity', 0))

                self.fuzzy_system.compute()
                score = float(self.fuzzy_system.output['recommendation'])
                fuzzy_scores.append((item, score))

            except Exception as e:
                print(f"Error computing recommendation for {
                      item.get('title', '')}: {e}")

        # Sort and return top recommendations
        ranked_items = sorted(fuzzy_scores, key=lambda x: x[1], reverse=True)
        return ranked_items[:10]
