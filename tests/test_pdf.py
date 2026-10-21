import unittest
from pathlib import Path
import tempfile
import shutil
from cep.io_json import read_and_validate_json
from cep.modes import run_calibration, run_monitoring
from cep.pdf_report import generate_process_pdf, generate_consolidated_pdf, consolidate_output_directory


class TestPDFReport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.calib_json = Path("exemplos/dados_calibracao_x.json")
        self.monit_json = Path("exemplos/dados_acompanhar_x.json")

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_process_pdf(self):
        data = read_and_validate_json(self.calib_json)
        res = run_calibration(data, allow_revision=True)
        pdf_path = self.temp_dir / "relatorio_teste.pdf"
        
        out = generate_process_pdf(res, pdf_path)
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 1000)

    def test_generate_consolidated_pdf(self):
        data_cal = read_and_validate_json(self.calib_json)
        res_cal = run_calibration(data_cal, allow_revision=True)

        data_mon = read_and_validate_json(self.monit_json)
        res_mon = run_monitoring(data_mon, use_kalman=True)

        entries = [(res_cal, None, None), (res_mon, None, None)]
        pdf_path = self.temp_dir / "relatorio_consolidado_teste.pdf"

        out = generate_consolidated_pdf(entries, pdf_path)
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()

