import unittest

from src.rules.fraud_rules import calcular_score_reglas, calcular_semaforo


class TestRules(unittest.TestCase):
    def test_semaforo_thresholds(self):
        self.assertEqual(calcular_semaforo(0), "VERDE")
        self.assertEqual(calcular_semaforo(41), "AMARILLO")
        self.assertEqual(calcular_semaforo(76), "ROJO")

    def test_score_reglas_returns_tuple(self):
        score, reasons = calcular_score_reglas({"cobertura": "ROBO", "dias_entre_ocurrencia_reporte": 10})
        self.assertIsInstance(score, int)
        self.assertIsInstance(reasons, list)
