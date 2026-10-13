import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).with_name('audit_migrations.py')
SPEC = importlib.util.spec_from_file_location('audit_migrations', PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MigrationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def files(self, *names):
        for name in names:
            (self.root / name).write_text('raise "must never execute this migration"\n')

    def test_contiguous_sequence_never_executes_ruby(self):
        self.files('001_first.rb', '002_second.rb')
        result = MODULE.audit(self.root)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['next_version'], 3)
        self.assertFalse(result['database_accessed'])

    def test_gap_disables_next_version(self):
        self.files('001_first.rb', '003_third.rb')
        result = MODULE.audit(self.root)
        self.assertIn('missing migration versions 2..2', result['errors'])
        self.assertIsNone(result['next_version'])

    def test_duplicate_integer_even_with_different_padding(self):
        self.files('001_first.rb', '0001_duplicate.rb')
        self.assertTrue(any('duplicate' in x for x in MODULE.audit(self.root)['errors']))

    def test_invalid_and_zero_versions(self):
        self.files('000_zero.rb', 'one_bad.rb')
        self.assertGreaterEqual(len(MODULE.audit(self.root)['errors']), 3)

    def test_large_number_does_not_expand_a_range(self):
        self.files('999999999999999999_huge.rb')
        self.assertEqual(len(MODULE.audit(self.root)['errors']), 1)

    def test_symlink_is_not_read(self):
        (self.root / '001_external.rb').symlink_to(self.root.parent / 'does-not-exist')
        self.assertIn('not a regular migration file: 001_external.rb', MODULE.audit(self.root)['errors'])

    def test_real_migration_directory(self):
        result = MODULE.audit(PATH.resolve().parents[1] / 'lib/legion/data/migrations')
        self.assertEqual(result['errors'], [])
        self.assertGreater(result['count'], 0)


if __name__ == '__main__':
    unittest.main()
