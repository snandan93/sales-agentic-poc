import unittest
from types import SimpleNamespace

from observability import summarize_trace


class ObservabilityTests(unittest.TestCase):
    def test_summarizes_tokens_and_calls(self):
        messages = [
            SimpleNamespace(
                type="ai",
                usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
                response_metadata={},
            ),
            SimpleNamespace(type="tool", name="get_team_target"),
            SimpleNamespace(
                type="ai",
                usage_metadata={"input_tokens": 125, "output_tokens": 15, "total_tokens": 140},
                response_metadata={},
            ),
        ]
        metrics = summarize_trace(messages, 1.234)
        self.assertEqual(metrics["input_tokens"], 225)
        self.assertEqual(metrics["output_tokens"], 25)
        self.assertEqual(metrics["total_tokens"], 250)
        self.assertEqual(metrics["llm_calls"], 2)
        self.assertEqual(metrics["tool_calls"], 1)
        self.assertEqual(metrics["tool_names"], ["get_team_target"])
        self.assertEqual(metrics["elapsed_seconds"], 1.23)


if __name__ == "__main__":
    unittest.main()
