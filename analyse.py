from itertools import combinations
from collections import defaultdict
import sys, json


def get_alphabet(words):
    return reduce(lambda x, y: x | y, map(set, words), set())


class ScratchCard(object):
    ALPHABET = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}
    EXPECTED_WORD_COUNT = 19
    EXPECTED_WORD_LETTER_COUNT = 97
    EXPECTED_GOOD_LETTER_COUNT = 20
    EXPECTED_BONUS_WORD_LENGTH = 6
    EXPECTED_BONUS_WORD_UNIQUE_LETTERS_COUNT = 5
    BAD_LETTER_COUNT = len(ALPHABET) - EXPECTED_GOOD_LETTER_COUNT
    EXPECTED_WORD_LENGTH_DISTRIBUTION = {3: 4, 4: 5, 5: 3, 6: 3, 7: 1, 8: 2, 9: 1}

    def __init__(self, card_data):
        """Initialise from `card_data` dictionary.

        card_data example:
        {
          "layout": [
            "vase..s..j.",
            "...aquarium",
            "aunt..g..d.",
            "d...d.enjoy",
            "j.plumb....",
            "a.o.b.r.use",
            "cope..u.s..",
            "e.c..esteem",
            "n.o.p.h.f.a",
            "turnip..u.n",
            "..n.e.jolly"
          ],
          "bonus": "leader",
          "good_letters": "wxrivdjafhuyqcsgtmlp",
          "double_letter": "j"
        }
        """
        assert len(self.ALPHABET) == len(set(self.ALPHABET))

        self.layout = card_data['layout']
        self.words = self.get_hwords_from_layout(self.layout) +\
                     self.get_hwords_from_layout(map(''.join, zip(*self.layout)))

        if len(self.words) != self.EXPECTED_WORD_COUNT:
            raise ValueError('Saw {:} words instead of expected {:}'.format(len(self.words), self.EXPECTED_WORD_COUNT))
        if sum(map(len, self.words)) != self.EXPECTED_WORD_LETTER_COUNT:
            raise ValueError('Sum of word lengths {:} instead of expected {:}'.format(sum(map(len, self.words)), self.EXPECTED_WORD_LETTER_COUNT))
        self.check_word_length_distribution(self.words)

        for w in self.words:
            if len(set(w) - self.ALPHABET) > 0:
                raise ValueError('Word {:} contains unexpected letter'.format(w))
        self.words_letters = get_alphabet(self.words)

        if len(card_data['good_letters']) != len(set(card_data['good_letters'])):
            raise ValueError('Good letters {:} not unique!'.format(card_data['good_letters']))
        if len(set(card_data['good_letters']) - self.ALPHABET) > 0:
            raise ValueError('Good letters {:} contains unexpected letter'.format(card_data['good_letters']))
        if len(card_data['good_letters']) != self.EXPECTED_GOOD_LETTER_COUNT:
            raise ValueError('Number of good letters {:} instead of expected {:}'.format(len(card_data['good_letters']), self.EXPECTED_GOOD_LETTER_COUNT))
        self.good_letters = card_data['good_letters']
        self.bad_letters = self.ALPHABET - set(self.good_letters)
        assert len(self.bad_letters) == self.BAD_LETTER_COUNT

        if len(card_data['bonus']) != self.EXPECTED_BONUS_WORD_LENGTH:
            raise ValueError('Bonus word {:} did not have expected length {:}'.format(card_data['bonus'], self.EXPECTED_BONUS_WORD_LENGTH))
        if len(set(card_data['bonus'])) != self.EXPECTED_BONUS_WORD_UNIQUE_LETTERS_COUNT:
            raise ValueError('Bonus word {:} did not have expected number of unique letters {:}'.format(card_data['bonus'], self.EXPECTED_BONUS_WORD_UNIQUE_LETTERS_COUNT))
        if len(set(card_data['bonus']) - self.ALPHABET) > 0:
            raise ValueError('Bonus word {:} contains unexpected letter'.format(card_data['bonus']))
        self.bonus = card_data['bonus']

        if len(card_data['double_letter']) != 1:
            raise ValueError('Double letter {:} should be single letter'.format(card_data['double_letter']))
        if card_data['double_letter'] not in card_data['good_letters']:
            raise ValueError('Double letter {:} not amongst good letters {:}'.format(card_data['double_letter'], card_data['good_letters']))
        if card_data['double_letter'] not in self.ALPHABET:
            raise ValueError('Double letter {:} is unexpected letter'.format(card_data['double_letter']))
        if card_data['double_letter'] in self.bonus:
            raise ValueError('Double letter {:} not expected to be in bonus word'.format(card_data['double_letter'], self.bonus))
        self.double_letter = card_data['double_letter']

    @classmethod
    def get_hwords_from_layout(cls, layout):
        return filter(lambda s: len(s) > 1, reduce(lambda l, s: l + s.split('.'), layout, []))

    @classmethod
    def check_word_length_distribution(cls, words):
        d = defaultdict(int)
        for w in words:
            d[len(w)] += 1
        assert sum([k*v for (k, v) in d.items()]) == cls.EXPECTED_WORD_LETTER_COUNT
        for (k, v) in cls.EXPECTED_WORD_LENGTH_DISTRIBUTION.items():
            if d[k] != v:
                raise ValueError('Words of length {:} occuring with frequency {:} instead of {:} expected'.format(k, d[k], v))

    @classmethod
    def is_good_word(cls, word, bad_letters):
        for l in bad_letters:
            if l in word:
                return False
        return True

    @classmethod
    def get_good_words(cls, words, bad_letters):
        return [w for w in words if cls.is_good_word(w, bad_letters)]

    @classmethod
    def get_bad_letter_distribution_for_words(cls, words):
        """For a given list of words, this returns the frequency of each score
        ranging over all possible bad letter possibilities.

        The idea is that the words are public information (i.e., available
        before scratching the card) and so if this distribution showed almost
        all bad letter combinations corresponded to winning cards then that is
        a positive. Or conversely, if there was no choice of bad letters that
        corresponded to, say, the top prize then this would be a negative.
        """
        d = defaultdict(int)
        for bad_letters in combinations(cls.ALPHABET, cls.BAD_LETTER_COUNT):
            d[len(cls.get_good_words(words, bad_letters))] += 1
        assert sum(d.values()) == 230230
        return dict(d)

    @classmethod
    def get_constrained_bad_letter_distribution_for_words(cls, words, double_letter, bonus):
        """Similar to `get_bad_letter_distribution_for_words` except restricting
        to choices of bad letters conforming to:
          * The `double_letter` is good (empirically true with > 99.9% confidence)
          * The `bonus` word is bad (cannot always be true but conservative
            assumption that cuts down combinations a lot)
        """
        d = defaultdict(int)
        for bad_letters in combinations(cls.ALPHABET, cls.BAD_LETTER_COUNT):
            if double_letter in bad_letters:
                continue
            if cls.is_good_word(bonus, bad_letters):
                continue
            d[len(cls.get_good_words(words, bad_letters))] += 1
        assert sum(d.values()) == 138340
        return dict(d)

    def get_card_score(self):
        good_words = self.get_good_words(self.words, self.bad_letters)
        return {
            'good_words': good_words,
            'doubled': self.double_letter in get_alphabet(good_words),
            'bonus': self.is_good_word(self.bonus, self.bad_letters)
            }


filename = sys.argv[1]
card = ScratchCard(json.load(open(filename)))
score = card.get_card_score()

print('{:}\t'\
      'score: {:}\t'\
      'doubled: {:}\t'\
      'bonus: {:}\t'\
      'squares used: {:}\t'\
      'good word letters: {:}\t'\
      'bad word letters: {:}\t'\
      'all word letters: {:}\t'\
      'non-word letters: {:}\t'
      'good words: {:}\t'\
      '{:}'.format(filename,
                   len(score['good_words']),
                   score['doubled'],
                   score['bonus'],
                   len(filter(lambda x: x != '.', ''.join(card.layout))),
                   len(set(card.words_letters) & set(card.good_letters)),
                   len(set(card.words_letters) & set(card.bad_letters)),
                   len(card.words_letters),
                   ''.join(sorted(ScratchCard.ALPHABET - set(card.words_letters))),
                   ','.join(score['good_words']),
                   card.get_bad_letter_distribution_for_words(card.words)))
