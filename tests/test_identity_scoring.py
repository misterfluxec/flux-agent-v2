import unittest
from src.services.identity_scoring_engine import IdentityScoringEngine

class TestIdentityScoring(unittest.TestCase):
    def test_phonetic_match_latam(self):
        # Escenario: "Muñoz" vs "Munoz" (Común en teclados sin Ñ o sistemas viejos)
        target = {"name": "Juan Muñoz", "phone": "593999999999"}
        candidate = {"id": "cust_1", "name": "Juan Munoz", "phone": "593999999999"}
        
        score = IdentityScoringEngine.calculate_match_score(target, candidate)
        print(f"\n[TEST] Score 'Muñoz' vs 'Munoz': {score}")
        self.assertGreaterEqual(score, 0.6) # Debería ser alto por fono + phone

    def test_levenshtein_typo(self):
        # Escenario: Error de dedo "Gonzales" vs "Gonzale"
        target = {"name": "Carlos Gonzales"}
        candidate = {"id": "cust_2", "name": "Carlos Gonzale"}
        
        score = IdentityScoringEngine.calculate_match_score(target, candidate)
        print(f"[TEST] Score 'Gonzales' vs 'Gonzale': {score}")
        self.assertGreater(score, 0.04) # Un poco de score por cercanía

    def test_exact_national_id(self):
        # Escenario: Misma cédula, diferente teléfono
        target = {"national_id": "1722222222", "phone": "1"}
        candidate = {"id": "cust_3", "national_id": "1722222222", "phone": "2"}
        
        score = IdentityScoringEngine.calculate_match_score(target, candidate)
        print(f"[TEST] Score National ID Match: {score}")
        self.assertEqual(score, 0.9) # Confianza máxima (0.9)

if __name__ == "__main__":
    unittest.main()
