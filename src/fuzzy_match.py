import jellyfish
import pybktree
import logging

logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, match_threshold=lambda s: 1 + 0.3 * len(s)):
        self.match_tree = pybktree.BKTree(jellyfish.damerau_levenshtein_distance)
        self.match_map = {}
        self.max_query_len = 0
        self.get_match_threshold = match_threshold

    def add(self, target: str, result, suppress_warning=False):
        """
        Adds a string as a match target, with a result object to map to it.
        :param target: target string to map to result object
        :param result: object to map, may not be None
        :param suppress_warning: suppress the generation of a warning in the case that the target string already exists
        """
        target_str = target.lower()
        if target_str in self.match_map:
            if not suppress_warning:
                logger.warning(f'Match string "{target_str}" already exists, ignoring new addition')
            return
        elif result is None:
            raise ValueError(f"Result may not be None")

        self.match_map[target_str] = result
        self.match_tree.add(target_str)
        self.max_query_len = max(self.max_query_len, len(target_str))

    def _get_match_strings(self, input_string: str):
        """
        Return all match keys for an input string
        :param input_string: string to match
        :return: all results, as a list of tuples (edit distance, result key)
        """
        match_threshold = self.get_match_threshold(input_string)
        return self.match_tree.find(input_string.lower(), match_threshold)

    def match(self, input_string: str):
        """
        Resolves and returns the closest match to a target string
        :param input_string: input string to match
        :return a tuple of (result object, match key, match quality as a fraction of threshold) if a match is found,
        else None
        """
        results = self._get_match_strings(input_string)
        if not results:
            return None
        else:
            match_distance, match_key = results[0]
            match_threshold = self.get_match_threshold(input_string)
            return self.match_map[match_key], match_key, 1 - match_distance / match_threshold


logger.info(f"Using {jellyfish.library} version of Jellyfish")
