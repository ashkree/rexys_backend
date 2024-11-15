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
            tfidf_matrix[item_index], tfidf_matrix[:len(self.items)]
        ).flatten()
        return np.mean(similarities)

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
        overall_score = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'overall_score')
        rating = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'rating')
        pop = ctrl.Antecedent(np.arange(0, 1000000, 1000), 'popularity')
        recommendation = ctrl.Consequent(np.arange(0, 1.1, 0.1), 'recommendation')

        overall_score.automf(3)
        rating.automf(3)
        pop.automf(3)

        recommendation['poor'] = fuzz.trimf(recommendation.universe, [0, 0, 0.5])
        recommendation['average'] = fuzz.trimf(recommendation.universe, [0.3, 0.5, 0.7])
        recommendation['good'] = fuzz.trimf(recommendation.universe, [0.5, 1, 1])

        rules = [
            ctrl.Rule(overall_score['high'] & rating['good'] & pop['high'], recommendation['good']),
            ctrl.Rule(overall_score['average'] & rating['average'] & pop['average'], recommendation['average']),
            ctrl.Rule(overall_score['poor'] & rating['poor'] & pop['low'], recommendation['poor']),
        ]

        ranking_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(ranking_ctrl)

    def calculate_preference_score(self, item, user_preferences):
        score = 0

        if 'genre' in user_preferences and 'genre' in item:
            movie_genres = [g.strip().lower() for g in item['genre'].split(',')]
            if user_preferences['genre'].lower() in movie_genres:
                score += self.weights['genre']

        if 'tags' in user_preferences and 'tags' in item:
            item_tags = [tag.strip().lower() for tag in item['tags']]
            pref_tags = [tag.strip().lower() for tag in user_preferences['tags']]
            matching_tags = set(item_tags).intersection(set(pref_tags))
            if pref_tags:
                score += self.weights['tags'] * len(matching_tags) / len(pref_tags)

        if 'rating' in user_preferences and 'rating' in item:
            min_rating = user_preferences['rating'].get('min', float('-inf'))
            max_rating = user_preferences['rating'].get('max', float('inf'))
            if min_rating <= item['rating'] <= max_rating:
                score += self.weights['rating']

        if 'actors' in user_preferences and 'actors' in item:
            item_actors = [actor.strip().lower() for actor in item['actors']]
            pref_actors = [actor.strip().lower() for actor in user_preferences['actors']]
            matching_actors = set(item_actors).intersection(set(pref_actors))
            if pref_actors:
                score += self.weights['actors'] * len(matching_actors) / len(pref_actors)

        return np.nan_to_num(score, nan=0)  # Ensure score is not NaN


    def recommend(self, user_preferences, user_history=None):
        if user_history is None:
            user_history = []

        try:
            available_items = [item for item in self.items if item not in user_history]
            print(f"Filtered available items count: {len(available_items)}")

            if not available_items:
                print("No available items after filtering.")
                return []

            tfidf_vectorizer = TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x)
            item_tags = [item.get('tags', []) for item in available_items if isinstance(item.get('tags', list))]

            if not item_tags or all(len(tags) == 0 for tags in item_tags):
                print("No valid tags for TF-IDF. Skipping similarity calculations.")
                return []

            tfidf_matrix = tfidf_vectorizer.fit_transform(item_tags)
            print("TF-IDF matrix generated.")

            scores = []
            for idx, item in enumerate(available_items):
                try:
                    preference_score = self.calculate_preference_score(item, user_preferences)
                    cb_score = self.calculate_cb_score(idx, tfidf_matrix)

                    overall_score = 0.7 * preference_score + 0.3 * cb_score
                    overall_score = np.nan_to_num(overall_score, nan=0.5)

                    rating = float(item.get('rating', 0))
                    popularity = float(min(item.get('popularity', 0), 1000000))

                    self.fuzzy_system.input['overall_score'] = max(0, min(overall_score, 1))
                    self.fuzzy_system.input['rating'] = max(0, min(rating, 10))
                    self.fuzzy_system.input['popularity'] = max(0, min(popularity, 1000000))

                    self.fuzzy_system.compute()
                    final_score = float(self.fuzzy_system.output['recommendation'])
                    final_score = np.nan_to_num(final_score, nan=0.5)

                    scores.append((item, final_score))

                except Exception as e:
                    print(f"Error processing item {item.get('title', 'Unknown')}: {e}")

            ranked_items = sorted(scores, key=lambda x: x[1], reverse=True)
            print(f"Final recommended count: {len(ranked_items)}")
            return ranked_items[:10]

        except Exception as e:
            print(f"Critical error in recommendation process: {e}")
            return []

class GameRecommender:
    def __init__(self, items):
        self.items = items
        self.weights = {
            'genre': 0.21,
            'tags': 0.20,
            'rating': 0.19,
            'cost': 0.19,
            'system_requirements': 0.21
        }
        self.fuzzy_system = self._create_fuzzy_system()

    def _create_fuzzy_system(self):
        rating = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'rating')
        cost = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'cost')
        popularity = ctrl.Antecedent(np.arange(0, 15000000, 100000), 'popularity')
        recommendation = ctrl.Consequent(np.arange(0, 1.1, 0.1), 'recommendation')

        rating.automf(3)  # low, medium, high
        cost.automf(3)    # cheap, moderate, expensive
        popularity.automf(3)  # low, medium, high

        recommendation['poor'] = fuzz.trimf(recommendation.universe, [0, 0, 0.5])
        recommendation['average'] = fuzz.trimf(recommendation.universe, [0.3, 0.5, 0.7])
        recommendation['excellent'] = fuzz.trimf(recommendation.universe, [0.5, 1, 1])

        rules = [
            ctrl.Rule(rating['good'] & cost['cheap'] & popularity['high'], recommendation['excellent']),
            ctrl.Rule(rating['good'] & cost['moderate'] & popularity['medium'], recommendation['good']),
            ctrl.Rule(rating['poor'] & cost['expensive'] & popularity['low'], recommendation['poor']),
            ctrl.Rule(rating['average'] & cost['moderate'] & popularity['high'], recommendation['average']),
            ctrl.Rule(rating['average'] & cost['cheap'] & popularity['medium'], recommendation['good']),
        ]

        ranking_ctrl = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(ranking_ctrl)

    def calculate_preference_score(self, item, user_preferences):
        score = 0

        # Genre Match
        if 'genre' in user_preferences and 'genre' in item:
            game_genres = [g.strip().lower() for g in item['genre'].split(',')]
            if user_preferences['genre'].lower() in game_genres:
                score += self.weights['genre']

        # Tags Match
        if 'tags' in user_preferences and 'tags' in item:
            item_tags = [tag.strip().lower() for tag in item['tags']]
            pref_tags = [tag.strip().lower() for tag in user_preferences['tags']]
            matching_tags = set(item_tags).intersection(set(pref_tags))
            if pref_tags:
                score += self.weights['tags'] * len(matching_tags) / len(pref_tags)

        # Rating Range Check
        if 'rating' in user_preferences and 'rating' in item:
            min_rating = user_preferences['rating'].get('min', float('-inf'))
            max_rating = user_preferences['rating'].get('max', float('inf'))
            if min_rating <= item['rating'] <= max_rating:
                score += self.weights['rating']

        # Cost Matching
        if 'cost' in user_preferences and 'cost' in item:
            max_cost = user_preferences['cost'].get('max', float('inf'))
            if item['cost'] <= max_cost:
                score += self.weights['cost']

        return np.nan_to_num(score, nan=0)  # Ensure score is not NaN

    def recommend(self, user_preferences, user_history=None):
        if user_history is None:
            user_history = []

        try:
            available_items = [item for item in self.items if item not in user_history]
            print(f"Filtered available items count: {len(available_items)}")

            if not available_items:
                print("No available items after filtering.")
                return []

            tfidf_vectorizer = TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x)
            item_tags = [item.get('tags', []) for item in available_items if isinstance(item.get('tags', list))]

            if not item_tags or all(len(tags) == 0 for tags in item_tags):
                print("No valid tags for TF-IDF. Skipping similarity calculations.")
                return []

            tfidf_matrix = tfidf_vectorizer.fit_transform(item_tags)
            print("TF-IDF matrix generated.")

            scores = []
            for idx, item in enumerate(available_items):
                try:
                    preference_score = self.calculate_preference_score(item, user_preferences)
                    cb_score = self.calculate_cb_score(idx, tfidf_matrix)

                    overall_score = 0.7 * preference_score + 0.3 * cb_score
                    overall_score = np.nan_to_num(overall_score, nan=0.5)

                    rating = float(item.get('rating', 0))
                    cost = float(item.get('cost', 0))
                    popularity = float(min(item.get('popularity', 0), 15000000))

                    self.fuzzy_system.input['rating'] = max(0, min(rating, 1))
                    self.fuzzy_system.input['cost'] = max(0, min(cost, 100))
                    self.fuzzy_system.input['popularity'] = max(0, min(popularity, 15000000))

                    self.fuzzy_system.compute()
                    final_score = float(self.fuzzy_system.output['recommendation'])
                    final_score = np.nan_to_num(final_score, nan=0.5)

                    scores.append((item, final_score))

                except Exception as e:
                    print(f"Error processing item {item.get('title', 'Unknown')}: {e}")

            ranked_items = sorted(scores, key=lambda x: x[1], reverse=True)
            print(f"Final recommended count: {len(ranked_items)}")
            return ranked_items[:10]

        except Exception as e:
            print(f"Critical error in recommendation process: {e}")
            return []

    def calculate_cb_score(self, item_index, tfidf_matrix):
        similarities = cosine_similarity(
            tfidf_matrix[item_index], tfidf_matrix[:len(self.items)]
        ).flatten()
        return np.mean(similarities)

