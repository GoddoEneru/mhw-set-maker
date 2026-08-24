import time

import pandas as pd
import numpy as np

from src.armor_set import ArmorSet


class SetMaker:
    """
    A class responsible for generating optimized armor sets based on user-defined skill preferences.

    This class loads cleaned armor, talisman, and skill data, filters relevant items,
    computes combinations of armor sets, and returns valid or optimal configurations
    based on defense or decoration potential.
    """

    _ARMOR_TYPES = ['head', 'chest', 'arm', 'waist', 'leg']

    _DEFENSE_SKILL_NAMES = [
        'Defense Boost', 'Dragon Resistance', 'Fire Resistance',
        'Ice Resistance', 'Thunder Resistance', 'Water Resistance',
    ]

    _DEFENSE_SKILL_MAX_LEVEL = {
        'Defense Boost': 5,
        'Dragon Resistance': 3,
        'Fire Resistance': 3,
        'Ice Resistance': 3,
        'Thunder Resistance': 3,
        'Water Resistance': 3,
    }

    _DEFENSE_BY_SKILLS = {
        'Defense Boost_lv0': (0, 0),
        'Defense Boost_lv1': (0, 5),
        'Defense Boost_lv2': (0, 10),
        'Defense Boost_lv3': (5 / 100, 10),
        'Defense Boost_lv4': (5 / 100, 20),
        'Defense Boost_lv5': (8 / 100, 20),
        'Dragon Resistance_lv0': (0, 0),
        'Dragon Resistance_lv1': (0, 0),
        'Dragon Resistance_lv2': (0, 0),
        'Dragon Resistance_lv3': (0, 10),
        'Fire Resistance_lv0': (0, 0),
        'Fire Resistance_lv1': (0, 0),
        'Fire Resistance_lv2': (0, 0),
        'Fire Resistance_lv3': (0, 10),
        'Ice Resistance_lv0': (0, 0),
        'Ice Resistance_lv1': (0, 0),
        'Ice Resistance_lv2': (0, 0),
        'Ice Resistance_lv3': (0, 10),
        'Thunder Resistance_lv0': (0, 0),
        'Thunder Resistance_lv1': (0, 0),
        'Thunder Resistance_lv2': (0, 0),
        'Thunder Resistance_lv3': (0, 10),
        'Water Resistance_lv0': (0, 0),
        'Water Resistance_lv1': (0, 0),
        'Water Resistance_lv2': (0, 0),
        'Water Resistance_lv3': (0, 10),
    }

    def __init__(self):
        self.df_armors = pd.read_csv("src/data/armors.csv")
        self.df_talismans = pd.read_csv("src/data/talismans.csv")
        self.df_skills = pd.read_csv("src/data/skills.csv")

    def add_decorations_score_col(self, df_armors):
        """
        Adds a 'Decorations_score' column to the armor DataFrame by summing
        the sizes of all available decoration slots.

        Args:
            df_armors (pandas.DataFrame): The armor data.

        Returns:
            pandas.DataFrame: The modified armor DataFrame with a new 'Decorations_score' column.
        """
        decoration_cols_names = ['Decoration_slot_1_size', 'Decoration_slot_2_size', 'Decoration_slot_3_size']
        df_armors[decoration_cols_names] = df_armors[decoration_cols_names].fillna(0)
        df_armors['Decorations_score'] = df_armors.apply(
            lambda x: x['Decoration_slot_1_size'] + x['Decoration_slot_2_size'] + x['Decoration_slot_3_size'], axis=1)
        return df_armors

    def filter_relevant_armors_and_talismans(self, skills, df_armors, df_talismans):
        """
        Filters armors and talismans to only include those with the desired skills.

        - Filters armors that provide any of the desired skills.
        - Filters and reduces talismans to one per skill with the highest level.

        Args:
            skills (list): List of skill names to search for.
            df_armors (pandas.DataFrame): Armor data.
            df_talismans (pandas.DataFrame): Talisman data.

        Returns:
            tuple:
                - pandas.DataFrame: Filtered armors.
                - pandas.DataFrame: Filtered talismans.
        """
        filter = df_armors['Skill_1_name'].isin(skills)\
            | df_armors['Skill_2_name'].isin(skills)\
            | df_armors['Skill_3_name'].isin(skills)
        filtered_df_armors = df_armors.loc[filter]

        skills = skills + ['Defense Boost']
        filter = df_talismans['Skill_name'].isin(skills)
        filtered_df_talismans = df_talismans.loc[filter]
        filtered_df_talismans = filtered_df_talismans.sort_values(by=['Skill_lvl'], ascending=False)
        filtered_df_talismans = filtered_df_talismans.groupby('Skill_name').apply(
            lambda x: x.iloc[0]).reset_index(drop=True)

        return filtered_df_armors, filtered_df_talismans

    def get_best_armor_for_each_type(self, df_armors, sort_on='defense'):
        """
        Retrieves the top-performing armor piece for each type (head, chest, etc.)
        based on the given sorting criteria.

        Args:
            df_armors (pandas.DataFrame): DataFrame of available armors.
            sort_on (str): Criteria to sort by; either 'defense' or 'decorations'.

        Returns:
            pandas.DataFrame: The best armor piece for each armor type.
        """
        sorted_df_armors = df_armors.copy()
        match sort_on:
            case "defense":
                sorted_df_armors = sorted_df_armors.sort_values(
                    by=['Defense', 'Decorations_score', 'Armor_type'], ascending=False)
            case "decorations":
                sorted_df_armors = sorted_df_armors.sort_values(
                    by=['Decorations_score', 'Defense', 'Armor_type'], ascending=False)

        df_best_armors = sorted_df_armors.groupby('Armor_type').apply(lambda x: x.iloc[0]).reset_index(drop=True)

        return df_best_armors

    def _apply_defense_bonus(self, defense, skills):
        """
        Computes the post-bonus defense value for a completed armor set's skills, by
        sequentially compounding the percentage/flat bonuses of any defense-related
        skill present (Defense Boost, elemental resistances), in alphabetical skill
        name order.

        Args:
            defense (int | float): The raw summed defense of the set.
            skills (dict): Skill name -> level for the completed set.

        Returns:
            int: The defense value after applying all defense-related skill bonuses.
        """
        for skill_name in self._DEFENSE_SKILL_NAMES:
            level = int(skills.get(skill_name, 0))
            percent_bonus, flat_bonus = self._DEFENSE_BY_SKILLS[f'{skill_name}_lv{level}']
            defense = defense + percent_bonus * defense + flat_bonus
        return round(defense)

    def _armor_skill_pairs(self, record):
        pairs = []
        for col in ('Skill_1', 'Skill_2', 'Skill_3'):
            name = record[f'{col}_name']
            if name is not np.nan:
                pairs.append((name, record[f'{col}_lvl']))
        return pairs

    def find_best_armor_set(self, filtered_df_armors, filtered_df_talismans, df_best_armors,
                            df_skills, necessary_skills, sort_on='defense', time_budget_seconds=5.0):
        """
        Searches for the single best armor set (head, chest, arm, waist, leg, talisman)
        given the candidate pools, using a depth-first branch-and-bound search over
        `ArmorSet` instead of enumerating every combination:
        - Branches where some skill already exceeds its max level are abandoned immediately
          (skill levels only ever accumulate, so such a branch can never become valid).
        - Branches that, even in the best possible case for their remaining slots, could not
          match or beat the best complete set found so far are abandoned too (branch-and-bound),
          using a precomputed upper bound on how much each requested skill's level could still
          grow from the slots/talisman not yet chosen.
        - Candidates within each slot are visited in an order likely to yield strong sets first,
          so a good bound is established early and prunes effectively.
        No DataFrame of combinations is ever built; only the best combination seen so far is kept.

        For the vast majority of requests (a handful of requested skills) this search finishes
        in well under a second and the result is exactly optimal. For pathological requests
        (many generic skills with generous level caps, so a huge number of combinations tie on
        skill levels) proving optimality can still take a long time even though a very strong
        set is found almost immediately; `time_budget_seconds` bounds how long the search keeps
        looking for a strictly better set before returning the best one found so far, so the UI
        never hangs. Set it to None to search exhaustively with no time limit.

        Args:
            filtered_df_armors (pandas.DataFrame): Filtered set of relevant armors.
            filtered_df_talismans (pandas.DataFrame): Filtered set of relevant talismans.
            df_best_armors (pandas.DataFrame): Best armor pieces by type to supplement combinations.
            df_skills (pandas.DataFrame): Skill data containing max level for each skill.
            necessary_skills (list): Skills required in the final armor set, in priority order.
            sort_on (str): Primary prioritization criterion after skills, 'defense' or 'decorations'.
            time_budget_seconds (float | None): Maximum search time before returning the best set
                found so far; None searches until every branch is resolved or pruned.

        Returns:
            pandas.DataFrame | None: A single-row DataFrame containing the best armor set,
            or None if no valid combination exists.
        """
        df_usable_armors = pd.concat([filtered_df_armors, df_best_armors]).drop_duplicates(subset=['Armor'])
        armors_by_type = {
            armor_type: df_usable_armors[df_usable_armors['Armor_type'] == armor_type].to_dict('records')
            for armor_type in self._ARMOR_TYPES
        }
        talismans = filtered_df_talismans.to_dict('records')
        skill_max_level = dict(zip(df_skills['Skill'], df_skills['skill_max_level']))
        necessary_skills_count = len(necessary_skills)

        # Weight earlier-priority requested skills far above later ones so ordering candidates
        # by this weighted score roughly mirrors the lexicographic sort used to pick the winner,
        # which lets a strong candidate solution (and a useful bound) be found early.
        skill_weights = {skill: 1000 ** (necessary_skills_count - idx) for idx, skill in enumerate(necessary_skills)}
        secondary_key = 'Decorations_score' if sort_on == 'decorations' else 'Defense'

        def armor_priority(record):
            weighted_skill_score = sum(
                skill_weights.get(name, 0) * level for name, level in self._armor_skill_pairs(record))
            return (weighted_skill_score, record[secondary_key])

        for records in armors_by_type.values():
            records.sort(key=armor_priority, reverse=True)
        talismans.sort(
            key=lambda record: skill_weights.get(record['Skill_name'], 0) * record['Skill_lvl'],
            reverse=True)

        # Bound skills covers every necessary skill (for the primary comparison) plus every
        # defense-related skill (needed to bound the post-bonus defense tie-break below), since
        # once necessary skills are tied at their cap the tie-break metrics decide the winner and
        # need their own bound to keep pruning effective.
        bound_skill_names = list(dict.fromkeys(necessary_skills + self._DEFENSE_SKILL_NAMES))

        # suffix_max_skills[i][skill] = the most `skill`'s level could still grow from armor slots
        # i..4 and the talisman, taken independently per slot (an admissible upper bound).
        talisman_max = {skill: 0 for skill in bound_skill_names}
        for record in talismans:
            name = record['Skill_name']
            if name in talisman_max:
                talisman_max[name] = max(talisman_max[name], record['Skill_lvl'])

        suffix_max_skills = [None] * (len(self._ARMOR_TYPES) + 1)
        suffix_max_skills[len(self._ARMOR_TYPES)] = talisman_max
        for i in range(len(self._ARMOR_TYPES) - 1, -1, -1):
            armor_type = self._ARMOR_TYPES[i]
            slot_max = {skill: 0 for skill in bound_skill_names}
            for record in armors_by_type[armor_type]:
                for name, level in self._armor_skill_pairs(record):
                    if name in slot_max:
                        slot_max[name] = max(slot_max[name], level)
            suffix_max_skills[i] = {
                skill: slot_max[skill] + suffix_max_skills[i + 1][skill] for skill in bound_skill_names
            }

        def suffix_max_sums(value_fn):
            suffix = [0] * (len(self._ARMOR_TYPES) + 1)
            for i in range(len(self._ARMOR_TYPES) - 1, -1, -1):
                armor_type = self._ARMOR_TYPES[i]
                slot_max = max((value_fn(record) for record in armors_by_type[armor_type]), default=0)
                suffix[i] = slot_max + suffix[i + 1]
            return suffix

        def dec1_count(record):
            decoration_cols = ('Decoration_slot_1_size', 'Decoration_slot_2_size', 'Decoration_slot_3_size')
            return sum(1 for col in decoration_cols if record[col] == 1)

        # Talismans never contribute defense/decorations, so these suffixes only cover armor slots.
        suffix_max_defense = suffix_max_sums(lambda record: record['Defense'])
        suffix_max_decorations_score = suffix_max_sums(lambda record: record['Decorations_score'])
        suffix_max_dec1 = suffix_max_sums(dec1_count)

        armor_set = ArmorSet()
        best = None  # (sort_key, snapshot dict) of the best complete set found so far
        deadline = None if time_budget_seconds is None else time.monotonic() + time_budget_seconds
        node_count = 0
        deadline_exceeded = False

        def within_skill_caps(skill_names):
            for name in skill_names:
                max_level = skill_max_level.get(name)
                if max_level is not None and armor_set.skills[name] > max_level:
                    return False
            return True

        def best_still_reachable(i):
            if best is None:
                return True
            skill_bound = tuple(
                min(
                    armor_set.skills.get(skill, 0) + suffix_max_skills[i][skill],
                    skill_max_level.get(skill, float('inf')))
                for skill in necessary_skills)
            defense_skill_bound = {
                skill: min(
                    armor_set.skills.get(skill, 0) + suffix_max_skills[i][skill],
                    self._DEFENSE_SKILL_MAX_LEVEL[skill])
                for skill in self._DEFENSE_SKILL_NAMES
            }
            bound_raw_defense = armor_set.defense + suffix_max_defense[i]
            bound_post_bonus_defense = self._apply_defense_bonus(bound_raw_defense, defense_skill_bound)
            bound_decorations_score = armor_set.decorations_score + suffix_max_decorations_score[i]
            bound_dec1 = armor_set.nb_decorations_size_1 + suffix_max_dec1[i]

            if sort_on == 'decorations':
                bound = skill_bound + (bound_decorations_score, bound_post_bonus_defense, bound_dec1)
            else:
                bound = skill_bound + (bound_post_bonus_defense, bound_decorations_score, bound_dec1)

            return bound >= best[0]

        def evaluate_leaf():
            nonlocal best
            post_bonus_defense = self._apply_defense_bonus(armor_set.defense, armor_set.skills)
            skill_levels = tuple(armor_set.skills.get(skill_name, 0) for skill_name in necessary_skills)
            if sort_on == 'decorations':
                sort_key = skill_levels + (
                    armor_set.decorations_score, post_bonus_defense, armor_set.nb_decorations_size_1)
            else:
                sort_key = skill_levels + (
                    post_bonus_defense, armor_set.decorations_score, armor_set.nb_decorations_size_1)

            if best is None or sort_key > best[0]:
                best = (sort_key, {
                    'head': armor_set.head,
                    'chest': armor_set.chest,
                    'arm': armor_set.arm,
                    'waist': armor_set.waist,
                    'leg': armor_set.leg,
                    'talisman': armor_set.talisman,
                    'defense': post_bonus_defense,
                    'skills': dict(armor_set.skills),
                    'nb_decorations_size_1': armor_set.nb_decorations_size_1,
                    'nb_decorations_size_2': armor_set.nb_decorations_size_2,
                    'nb_decorations_size_3': armor_set.nb_decorations_size_3,
                    'decorations_score': armor_set.decorations_score,
                })

        def deadline_reached():
            nonlocal node_count, deadline_exceeded
            if deadline_exceeded:
                return True
            if deadline is None:
                return False
            node_count += 1
            if node_count % 4096 == 0 and time.monotonic() > deadline:
                deadline_exceeded = True
            return deadline_exceeded

        def search(i):
            if deadline_reached():
                return
            if not best_still_reachable(i):
                return
            if i < len(self._ARMOR_TYPES):
                armor_type = self._ARMOR_TYPES[i]
                for record in armors_by_type[armor_type]:
                    armor_set.update_armors(armor_type=armor_type, df_armors_filtered_by_type=record)
                    if within_skill_caps(name for name, _ in self._armor_skill_pairs(record)):
                        search(i + 1)
                    armor_set.revert_armors(armor_type=armor_type, df_armors_filtered_by_type=record)
            else:
                for record in talismans:
                    armor_set.update_talisman(record)
                    if within_skill_caps([record['Skill_name']]):
                        evaluate_leaf()
                    armor_set.revert_talisman(record)

        search(0)

        if best is None:
            return None

        return pd.json_normalize(best[1], sep='_')
