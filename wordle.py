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
    return read_file_to_list('dictionary.txt')


@dataclass
class GameResult:
    solution: str 
    guesses: int


class Color(Enum):
    GREY = 1
    YELLOW = 2
    GREEN = 2


@dataclass
class FeedbackLetter:
    letter: str
    color: Color = Color.GREY


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

    def reveal(self, word: str):
        assert len(word) == 5
        letters = []
        for i in range(len(word)):
            letter = word[i]
            feedback_letter = FeedbackLetter(letter = letter)
            if letter == self.solution[i]:
                feedback_letter.color = Color.GREEN
            elif letter in self.solution:
                feedback_letter.color = Color.YELLOW
            letters.append(feedback_letter)
        return letters


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

    def give_feedback(self):
        pass

    
def is_solution(letters: list[FeedbackLetter]):
    return len(letters) == 5 and all(letter.color == Color.GREEN for letter in letters)


def play_wordle_with_known_solution(solution: str) -> GameResult:
    return play_wordle(RandomGuessGenerator(get_dictionary()), KnownSolutionFeedbackProvider(solution))


def play_wordle(guess_generator, feedback_provider) -> GameResult:
    guesses = 1
    guess_feedback = []

    while not is_solution(guess_feedback):
        guess = guess_generator.guess()
        guess_feedback = feedback_provider.reveal(guess)
        guess_generator.give_feedback(guess_feedback)
        guesses += 1

    assert is_solution(guess_feedback)
    game_result = GameResult(guesses=guesses,solution=''.join(map(lambda x: x.letter, guess_feedback)))
    print_game_result(game_result)
    return game_result


class AggregateStats:
    def __init__(self):
        self.games_played = 0
        self.total_guesses = 0
        self.worst = 0
        self.best = sys.maxsize

    def include(self, result: GameResult):
        self.games_played += 1
        guesses = result.guesses
        self.total_guesses += guesses
        if guesses < self.best: self.best = guesses
        if guesses > self.worst: self.worst = guesses
    
    def average(self):
        return self.total_guesses / self.games_played

    def worst(self):
        return self.worst
    
    def best(self):
        return self.best

    def print_summary(self):
        print('\n\n ~~~')
        print('Played {} games.'.format(self.games_played))
        print('Best score: {}'.format(self.best))
        print('Worst score: {}'.format(self.worst))
        print('Mean score: {:.1f}'.format(self.average()))
        print(' ~~~ \n\n')

        with open('progress.csv', 'a') as file:
            file.write('{:.1f},{},{},{}\n'.format(self.average(), self.best, self.worst, datetime.datetime.now()))

    

def test_against_all_known_solutions():
    solutions = get_past_solutions()
    stats = AggregateStats()
    for solution in solutions:
        stats.include(play_wordle_with_known_solution(solution))
    stats.print_summary()


test_against_all_known_solutions()