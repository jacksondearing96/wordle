import datetime
from email import feedparser
import random
from dataclasses import dataclass
from enum import Enum
import sys
import copy

YELLOW_BONUS_FACTOR = 15

def read_file_to_list(filename):
    lines = []
    with open(filename) as file:
        while line := file.readline():
            lines.append(line.strip().upper())
    return lines


def get_past_solutions():
    return read_file_to_list('solutions.txt')


def get_dictionary():
    return read_file_to_list('sorted_dictionary.txt')


@dataclass
class GameResult:
    solution: str 
    guesses: int


class Color(Enum):
    GREY = 1
    YELLOW = 2
    GREEN = 3

def to_color_letter(c: Color) -> str:
    if c is Color.GREY: return 'g'
    if c is Color.YELLOW: return 'Y'
    if c is Color.GREEN: return 'G'


@dataclass
class FeedbackLetter:
    letter: str
    color: Color = Color.GREY
    position: int = -1


class Feedback:

    def __init__(self, word: str):
        self.letters: list[FeedbackLetter] = []
        for i in range(0, len(word)):
            self.append(word[i], position=i)

    def append(self, letter: str, position: int = -1, color: Color = Color.GREY):
        self.letters.append(FeedbackLetter(letter=letter,position=position,color=color))

    def colored_of(self, letter: str) -> int:
        return len(list(filter(lambda l, letter=letter: l.color is not Color.GREY and l.letter == letter, self.letters)))

    def to_word(self) -> str:
        return ''.join(map(lambda x: x.letter, self.letters))

    def to_color_str(self) -> str:
        return ''.join(map(lambda x: to_color_letter(x.color), self.letters))

    def is_solution(self):
        return len(self.letters) == 5 and all(l.color == Color.GREEN for l in self.letters)


def print_game_result(game_result: GameResult):
    print('🤖 WoBo found the solution!')
    print('Found solution: {}'.format(game_result.solution))
    print('Guesses required: {}'.format(game_result.guesses))


class FeedbackProvider:
    def reveal(self, word: str):
        pass


class KnownSolutionFeedbackProvider:

    def __init__(self, solution):
        self.solution = solution

    def _should_be_yellow(self, letters: list[FeedbackLetter], letter: str) -> bool:
        solution_count = self.solution.count(letter)
        color_letters = filter(lambda x: x.color is not Color.GREY, letters)
        color_count = ''.join(map(lambda x: x.letter, color_letters)).count(letter)
        return solution_count > color_count

    def reveal(self, word: str) -> Feedback:
        if len(word) != 5:
            print(word)
            assert len(word) == 5
        feedback = Feedback(word)

        for i in range(0, len(word)):
            if word[i] == self.solution[i]:
                feedback.letters[i].color = Color.GREEN
                feedback.letters[i].position = i

        for i in range(0, len(word)):
            if feedback.letters[i].color is Color.GREEN:
                continue
            if self._should_be_yellow(feedback.letters, word[i]):
                feedback.letters[i].color = Color.YELLOW
                feedback.letters[i].position = i
        return feedback
    


class GuessGenerator:
    def guess(self):
        pass


class RandomGuessGenerator:

    def __init__(self, dictionary):
        self.possible_solutions = copy.deepcopy(dictionary)

    def guess(self):
        random_guess = random.choice(self.possible_solutions)
        return random_guess

    def learn(self, feedback):
        pass


class BasicGuessGenerator:

    def __init__(self, dictionary: list[str]):
        self.guess_count = 1
        self.possible_solutions = copy.deepcopy(dictionary)
        self.dictionary = copy.deepcopy(dictionary)
        self.feedback_history = {
            Color.GREY: {},
            Color.YELLOW: {},
            Color.GREEN: {}
        }
        # with open('sorted_dictionary.txt', 'w') as f:
        #     self.score_sort()
        #     for w in self.possible_solutions:
        #         f.write(w + '\n')
            
        # rank letters
        # 

    def feedback_history_for_testing(self):
        return self.feedback_history

    def guess(self):
        if len(self.possible_solutions) == 0:
            print('*** ERROR *** No more possibilities!')
        
        if self.guess_count == 1:
            # best_guess = 'ADIEU'
            best_guess = self.best_eliminator_word_2()
        elif len(self.possible_solutions) > 3:
            best_guess = self.best_eliminator_word_2()
        else:
            best_guess = self.possible_solutions[0]

        self.guess_count += 1
        return best_guess

    # def best_eliminator_word(self) -> str:
    #     frequencies = map(lambda x: x[0], self.letter_frequencies_in_possible_solutions())
    #     non_green_frequencies = list(filter(lambda x: x not in self.feedback_history[Color.GREEN], frequencies))

    #     valuable_letters = {}
    #     for _ in range(0, 4):
    #         valuable_letters[non_green_frequencies[0]] = True
    #         non_green_frequencies.pop(0)

    #     MATCHES_REQUIRED = 4
    #     iter = 1
    #     while True:
    #         if iter == 3:
    #             MATCHES_REQUIRED = 3
    #         for word in self.dictionary:
    #             letter_matches = 0
    #             for l in word:
    #                 if l in valuable_letters:
    #                     letter_matches += 1
    #             if letter_matches >= MATCHES_REQUIRED:
    #                 return word
    #         valuable_letters[non_green_frequencies[0]] = True
    #         non_green_frequencies.pop(0)
    #         iter += 1

    def have_seen(self, letter: str, color: Color):
        return letter in self.feedback_history[color]

    def have_seen_at(self, letter: str, color: Color, position: int):
        return self.have_seen(letter, color) and position in self.feedback_history[color][letter]

    def best_eliminator_word_2(self) -> str:
        frequencies : list[self.LetterFrequency] = self.frequencies_map()
        word_scores = []

        for word in self.dictionary:
            score = 0
            seen_letters = {}
            for i in range(0, len(word)):
                l = word[i]
                if self.have_seen_at(l, Color.GREEN, i):
                    # This letter in this position is known solution.
                    # Introduce a small additional score to distinguish from GREY
                    score += 0.1
                elif self.have_seen_at(l, Color.YELLOW, i):
                    # Known YELLOW spot for this letter, no value in trying it again here.
                    continue
                elif self.have_seen_at(l, Color.GREY, i):
                    # This letter isn't in solution HERE, don't get any value from this.
                    continue
                elif l in seen_letters:
                    # Double letter, don't score this highly.
                    continue
                elif self.have_seen(l, Color.GREEN):
                    continue
                elif self.have_seen(l, Color.YELLOW):
                    # This could be the right spot for this letter known to be in the solution.
                    # Value here.
                    global YELLOW_BONUS_FACTOR
                    score += frequencies[l].frequency * YELLOW_BONUS_FACTOR
                else:
                    # Haven't tried this letter yet.
                    # Rank it based on frequency.
                    if l in frequencies:
                        score += frequencies[l].frequency + frequencies[l].positional_frequency[i]
                seen_letters[l] = True

            word_scores.append((word, score))
        
        word_scores = sorted(word_scores, key=lambda x: x[1], reverse=True)
        return word_scores[0][0]

    class LetterFrequency:
        def __init__(self, letter: str):
            self.letter: str = letter
            self.frequency: int = 0
            self.positional_frequency: list[int] = [0,0,0,0,0]

        def add_positional_frequency(self, position: int):
            self.positional_frequency[position] += 1

        def add_total_frequency(self):
            self.frequency += 1

    def frequencies_map(self):

        letters_to_frequencies = {}
        for word in self.possible_solutions:
            unique_letters = {}
            for i in range(0, len(word)):
                l = word[i]
                unique_letters[l] = 1
                if l not in letters_to_frequencies:
                    letters_to_frequencies[l] = self.LetterFrequency(letter=l)
                letters_to_frequencies[l].add_positional_frequency(i)
            for l in unique_letters:
                letters_to_frequencies[l].add_total_frequency()
                
        return letters_to_frequencies

    def letter_frequencies_in_possible_solutions(self):
        '''Returns a tuple of (letter, frequency) for each letter in possible_solutions.'''
        letters_and_counts = self.frequencies_map() 
        ret = []
        for l in letters_and_counts:
            ret.append((l, letters_and_counts[l]))
        ret = sorted(ret, key=lambda x: x[1], reverse=True)
        return ret

    def score_sort(self):
        self.possible_solutions = sorted(self.possible_solutions, key=lambda x: self.learn_score(x), reverse=True)

    def learn_score(self, word: str) -> int:
        hard_matches = 0
        for i in range(0, len(word)):
            hard_matches += len(list(filter(lambda w, i=i, l=word[i]: w[i] == l, self.possible_solutions)))
        soft_matches = 0
        for i in range(0, len(word)):
            soft_matches += len(list(filter(lambda w, i=i, l=word[i]: l in w, self.possible_solutions)))
        return 4 * hard_matches + soft_matches

    def add_feedback_history(self, feedback_letter: FeedbackLetter, position: int):
        color = feedback_letter.color
        letter = feedback_letter.letter
        if letter not in self.feedback_history[color]:
            self.feedback_history[color][letter] = {}
        self.feedback_history[color][letter][position] = True
        # Remove from YELLOW history if need be.
        # TODO fix this! This shouldn't be indiscriminent.
        if color == Color.GREEN and letter in self.feedback_history[Color.YELLOW]: # and position in self.feedback_history[Color.YELLOW][letter]:
            del self.feedback_history[Color.YELLOW][letter]

    def imply_greens(self):
        universals = [True, True, True, True, True]
        for i in range(1, len(self.possible_solutions)):
            prev = self.possible_solutions[i - 1]
            word = self.possible_solutions[i]
            for j in range(0, len(prev)):
                universals[j] = universals[j] and prev[j] == word[j]
            if len(list(filter(lambda x: not x, universals))) == 5:
                return
        for i in range(0, len(universals)):
            if universals[i]:
                feedback_letter = FeedbackLetter(letter=self.possible_solutions[0][i], color=Color.GREEN, position=i)
                self.add_feedback_history(feedback_letter, i)



        

    def learn(self, feedback: Feedback):
        if not feedback.is_solution():
            if feedback.to_word() in self.possible_solutions:
                self.possible_solutions.remove(feedback.to_word())
        for i in range(0, len(feedback.letters)):
            letter = feedback.letters[i]
            if letter.color is Color.GREY:
                # Remove words with too many of this letter.
                enough = feedback.colored_of(letter.letter)
                self._remove_words_with_excess(letter.letter, enough)
                # Remove words with this letter in this known bad spot.
                self.possible_solutions = list(filter(lambda w, letter=letter.letter, i=i: w[i] != letter, self.possible_solutions))
            elif letter.color is Color.GREEN:
                self.possible_solutions = list(filter(lambda w, l=letter, i=i: w[i] == l.letter, self.possible_solutions))
            else: # YELLOW 
                # TODO: Missing filter here!!!
                self.possible_solutions = list(filter(lambda w, l=letter.letter, i=i: l in w and w[i] != l, self.possible_solutions))
            self.add_feedback_history(letter, i)
        self.imply_greens()
        self.score_sort()

    def _remove_words_with_excess(self, letter: str, enough: int):
        self.possible_solutions = list(filter(lambda w, letter=letter, enough=enough: w.count(letter) <= enough, self.possible_solutions))

    def possible_solutions_for_testing(self) -> list[str]:
        return copy.deepcopy(self.possible_solutions)


def play_wordle_with_known_solution(solution: str) -> GameResult:
    result = play_wordle(BasicGuessGenerator(get_dictionary()), KnownSolutionFeedbackProvider(solution))
    print(solution + ': ' + str(result.guesses))
    return result


def play_wordle(guess_generator, feedback_provider) -> GameResult:
    guesses = 0
    feedback = None

    while guesses == 0 or not feedback.is_solution():
        guess = guess_generator.guess()
        feedback = feedback_provider.reveal(guess)
        guess_generator.learn(feedback)
        guesses += 1

    assert feedback.is_solution()
    game_result = GameResult(guesses=guesses,solution=feedback.to_word())
    # print_game_result(game_result)
    return game_result


class AggregateStats:
    def __init__(self):
        self.games_played = 0
        self.total_guesses = 0
        self.worst = 0
        self.best = sys.maxsize
        self.fails = 0

    def include(self, result: GameResult):
        self.games_played += 1
        guesses = result.guesses
        self.total_guesses += guesses
        if guesses < self.best: self.best = guesses
        if guesses > self.worst: self.worst = guesses
        if guesses > 6: self.fails += 1
    
    def average(self):
        return self.total_guesses / self.games_played

    def worst(self):
        return self.worst
    
    def best(self):
        return self.best

    def failure_rate(self):
        return self.fails / self.games_played

    def print_summary(self):
        print('\n\n ~~~')
        print('Played {} games.'.format(self.games_played))
        print('Best score: {}'.format(self.best))
        print('Worst score: {}'.format(self.worst))
        print('Failure rate: {:.3}'.format(self.failure_rate()))
        print('Mean score: {:.1f}'.format(self.average()))
        print(' ~~~ \n\n')

        with open('progress.csv', 'a') as file:
            file.write('{:.1f},{},{},{},{:.3}\n'.format(self.average(), self.best, self.worst, datetime.datetime.now(), self.failure_rate()))

    

def test_against_all_known_solutions():
    solutions = get_past_solutions()
    stats = AggregateStats()
    for solution in solutions:
        stats.include(play_wordle_with_known_solution(solution))
    stats.print_summary()
    return stats.average()


def experiment():
    for i in range(1, 100, 10):
        global YELLOW_BONUS_FACTOR
        YELLOW_BONUS_FACTOR = i
        mean = test_against_all_known_solutions()
        print(str(i) + ":" + str(mean))



if __name__ == '__main__':
    # experiment()
    # play_wordle_with_known_solution('FOUND')
    test_against_all_known_solutions()
    # print((2 * 2 + 17 * 3 + 23 * 4 + 10 * 5 + 9 * 6) / 63)
    # BasicGuessGenerator(ge=t_dictionary())