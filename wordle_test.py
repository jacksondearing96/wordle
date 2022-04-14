import unittest
from wordle import Feedback, FeedbackLetter, Color, KnownSolutionFeedbackProvider, to_color_letter, BasicGuessGenerator

class WordleTest(unittest.TestCase):

    def test_known_solution_feedback_provider(self):
        feedback_provider = KnownSolutionFeedbackProvider('TENET')
        self.assertEqual(feedback_provider.reveal('TENET').to_color_str(), 'GGGGG')
        self.assertEqual(feedback_provider.reveal('HELLO').to_color_str(), 'gGggg')
        self.assertEqual(feedback_provider.reveal('EENET').to_color_str(), 'gGGGG')
        self.assertEqual(feedback_provider.reveal('ZZTZZ').to_color_str(), 'ggYgg')
        self.assertEqual(feedback_provider.reveal('EEZZN').to_color_str(), 'YGggY')


    def test_to_color_str(self):
        self.assertEqual(to_color_letter(Color.GREY), 'g')
        self.assertEqual(to_color_letter(Color.YELLOW), 'Y')
        self.assertEqual(to_color_letter(Color.GREEN), 'G')


    def test_feedback_class(self):
        feedback = Feedback('HELLO')
        feedback.letters[2].color = Color.GREEN
        feedback.letters[3].color = Color.YELLOW
        feedback.letters[4].color = Color.GREY

        self.assertEqual(feedback.to_word(), 'HELLO')
        self.assertEqual(feedback.to_color_str(), 'ggGYg')
        self.assertEqual(feedback.colored_of('E'), 0)
        self.assertEqual(feedback.colored_of('L'), 2)

        self.assertFalse(feedback.is_solution())
        feedback.letters[0].color = Color.GREEN
        feedback.letters[1].color = Color.GREEN
        feedback.letters[2].color = Color.GREEN
        feedback.letters[3].color = Color.GREEN
        feedback.letters[4].color = Color.GREEN
        self.assertTrue(feedback.is_solution())

    def test_basic_guess_generator(self):
        generator = BasicGuessGenerator([
            'HELLO',
            'HALES',
            'HELAS',
            'WORLD',
            'DEPOT',
            'HELXX',
            'CHOKE',
            'HALED',
            'HXLEX'
        ])

        self.assertEqual(len(generator.possible_solutions_for_testing()), 9)

        # Pretend solution is HALES
        feedback = Feedback('HELLO')
        feedback.letters[0].color = Color.GREEN
        feedback.letters[1].color = Color.YELLOW
        feedback.letters[2].color = Color.GREEN
        generator.learn(feedback)

        filtered_list = generator.possible_solutions_for_testing()
        self.assertEqual(filtered_list, [ 
            'HALES',
            'HALED',
            'HXLEX'
        ])


if __name__ == '__main__':
    unittest.main()