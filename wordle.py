import datetime
import random
from dataclasses import dataclass
from enum import Enum
import sys
import copy

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


class Feedback:

    def __init__(self, word: str):
        self.letters: list[FeedbackLetter] = []
        for i in range(0, len(word)):
            self.append(word[i])

    def append(self, letter: str, color: Color = Color.GREY):
        self.letters.append(FeedbackLetter(letter=letter,color=color))

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
        assert len(word) == 5
        feedback = Feedback(word)

        for i in range(0, len(word)):
            if word[i] == self.solution[i]:
                feedback.letters[i].color = Color.GREEN

        for i in range(0, len(word)):
            if feedback.letters[i].color is Color.GREEN:
                continue
            if self._should_be_yellow(feedback.letters, word[i]):
                feedback.letters[i].color = Color.YELLOW
        return feedback
    


class GuessGenerator:
    def guess(self):
        pass


class RandomGuessGenerator:

    def __init__(self, dictionary):
        self.possible_solutions = copy.deepcopy(dictionary)

    def guess(self):
        random_guess = random.choice(self.possible_solutions)
        self.possible_solutions.remove(random_guess)
        return random_guess

    def learn(self, feedback):
        pass


class BasicGuessGenerator:

    def __init__(self, dictionary: list[str]):
        self.possible_solutions = copy.deepcopy(dictionary)
        # with open('sorted_dictionary.txt', 'w') as f:
        #     self.score_sort()
        #     for w in self.possible_solutions:
        #         f.write(w + '\n')
            

    def guess(self):
        if len(self.possible_solutions) == 0:
            print('*** ERROR *** No more possibilities!')
        best_guess = self.possible_solutions[0]
        self.possible_solutions.pop(0)
        return best_guess

    def score_sort(self):
        self.possible_solutions = sorted(self.possible_solutions, key=lambda x: self.learn_score(x), reverse=True)

    def learn_score(self, word: str) -> int:
        hard_matches = 0
        for i in range(0, len(word)):
            hard_matches += len(list(filter(lambda w, i=i, l=word[i]: w[i] == l, self.possible_solutions)))
        soft_matches = 0
        for i in range(0, len(word)):
            soft_matches += len(list(filter(lambda w, i=i, l=word[i]: l in w, self.possible_solutions)))
        return 2 * hard_matches + soft_matches


    def learn(self, feedback: Feedback):
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
                self.possible_solutions = list(filter(lambda w, l=letter, i=i: w[i] != l.letter, self.possible_solutions))
        self.score_sort()

    def _remove_words_with_excess(self, letter: str, enough: int):
        self.possible_solutions = list(filter(lambda w, letter=letter, enough=enough: w.count(letter) <= enough, self.possible_solutions))

    def possible_solutions_for_testing(self) -> list[str]:
        return copy.deepcopy(self.possible_solutions)


def play_wordle_with_known_solution(solution: str) -> GameResult:
    print(solution)
    return play_wordle(BasicGuessGenerator(get_dictionary()), KnownSolutionFeedbackProvider(solution))


def play_wordle(guess_generator, feedback_provider) -> GameResult:
    guesses = 1
    feedback = None

    while guesses == 1 or not feedback.is_solution():
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
        print('Failure rate: {}'.format(self.failure_rate()))
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


if __name__ == '__main__':
    test_against_all_known_solutions()
    # BasicGuessGenerator(get_dictionary())