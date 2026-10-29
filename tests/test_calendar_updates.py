import importlib.util,json,sqlite3,tempfile,threading,unittest,hashlib,io
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('calendar_updates',ROOT/'calendar_updates.py')
updates=importlib.util.module_from_spec(spec);spec.loader.exec_module(updates)

class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.data=self.root/'local-data';self.data.mkdir()
        (self.root/'app-release.json').write_text(json.dumps({'version':'0.3.0','installerUpdates':True}))
        self.manager=updates.UpdateManager(self.root,self.data,threading.Lock())

    def test_version_order_and_rejected_tags(self):
        self.assertGreater(updates.version('0.10.0'),updates.version('0.9.9'))
        for text in ['1.2','../setup.exe','1.2.3-beta','https://other.invalid']:
            with self.assertRaises(ValueError):updates.version(text)

    def test_startup_cache_and_manual_recheck(self):
        with patch.object(updates,'fetch_latest',return_value='0.3.1') as fetch:
            self.assertEqual(self.manager.check(True)['phase'],'available')
            self.manager.check(True);self.assertEqual(fetch.call_count,1)
            self.manager.check(False);self.assertEqual(fetch.call_count,2)
        fresh=updates.UpdateManager(self.root,self.data,threading.Lock())
        with patch.object(updates,'fetch_latest',side_effect=AssertionError('Must use cache')):
            self.assertEqual(fresh.check(True)['phase'],'available')

    def test_offline_does_not_claim_up_to_date(self):
        with patch.object(updates,'fetch_latest',side_effect=OSError('Offline')):
            self.assertEqual(self.manager.check()['phase'],'unavailable')

    def test_current_only_after_success_and_version_changes(self):
        self.assertEqual(self.manager.status()['phase'],'unknown')
        with patch.object(updates,'fetch_latest',return_value='0.3.0'):
            self.assertEqual(self.manager.check()['phase'],'current')
        (self.root/'app-release.json').write_text(json.dumps({'version':'0.3.1','installerUpdates':True}))
        self.assertEqual(self.manager.status()['currentVersion'],'0.3.1')

    def test_backup_restores_all_document_fields_including_pictures(self):
        doc={'id':'work:2026-10-29','kind':'day','date':'2026-10-29','html':'<p>SAMPLE ABC</p><img src="data:image/png;base64,AAAA">','layers':['SAMPLE ABC'],'teamLayers':[True],'taskColors':['#137333'],'completedLayers':[False]}
        with closing(sqlite3.connect(self.data/'calendar.sqlite')) as db:
            db.execute('CREATE TABLE documents (id TEXT PRIMARY KEY,body TEXT,revision INTEGER)')
            db.execute('INSERT INTO documents VALUES(?,?,?)',(doc['id'],json.dumps(doc),1))
            db.commit()
        with patch.object(updates,'fetch_latest',return_value='0.3.1'),patch.object(updates.webbrowser,'open',return_value=True) as opened:
            result=self.manager.open_installer()
            self.assertTrue(result['backupCreated']);opened.assert_called_once_with('https://github.com/BlessedHero/sunny-calendar/releases/download/v0.3.1/Sunny-Calendar-Setup.exe',new=2)
        files=list((self.data/'backups').glob('*.json'));self.assertEqual(len(files),1)
        backup=json.loads(files[0].read_text());self.assertEqual(backup['format'],'sunny-calendar-backup');self.assertEqual(backup['docs'],[doc])
        with closing(sqlite3.connect(self.data/'calendar.sqlite')) as db:self.assertEqual(json.loads(db.execute('SELECT body FROM documents').fetchone()[0]),doc)

    def test_no_open_on_failed_backup_or_working_copy(self):
        with patch.object(updates,'fetch_latest',return_value='0.3.1'),patch.object(self.manager,'backup',side_effect=OSError('Disk full')),patch.object(updates.webbrowser,'open') as opened:
            with self.assertRaises(OSError):self.manager.open_installer()
            opened.assert_not_called()
        (self.root/'app-release.json').write_text(json.dumps({'version':'0.3.0','installerUpdates':False}))
        with patch.object(updates.webbrowser,'open') as opened:
            with self.assertRaises(ValueError):self.manager.open_installer()
            opened.assert_not_called()

    def test_redirects_cannot_leave_https_github_api(self):
        handler=updates.GitHubRedirects()
        for url in ['http://api.github.com/x','https://other.invalid/x','https://api.github.com:8443/x','https://user:password@api.github.com/x']:
            with self.assertRaises(ValueError):handler.redirect_request(None,None,302,'',{},url)

    def test_preparation_downloads_verified_installer_and_makes_backup(self):
        body=b'MZ FICTIONAL INSTALLER TEST';release={'version':'0.3.1','size':len(body),'sha256':hashlib.sha256(body).hexdigest(),'url':updates.installer_url('0.3.1')}
        def download(info,path):path.write_bytes(body)
        with patch.object(updates,'fetch_release',return_value=release),patch.object(updates,'download_installer',side_effect=download):
            value=self.manager.prepare_installer()
            self.assertTrue(value['prepared']);self.assertTrue(value['backupCreated'])
            self.assertEqual(Path(self.manager.prepared['installer']).read_bytes(),body)
        with patch.object(updates,'native_process_matches',return_value=False),patch.object(updates.subprocess,'Popen') as started:
            (self.root/'unins000.exe').touch()
            with self.assertRaises(ValueError):self.manager.launch_installer(123)
            started.assert_not_called()

    def test_wrong_download_digest_never_becomes_installer(self):
        body=b'MZ FICTIONAL DOWNLOAD';release={'version':'0.3.1','size':len(body),'sha256':'0'*64,'url':updates.installer_url('0.3.1')}
        fake=unittest.mock.MagicMock();fake.open.return_value=io.BytesIO(body)
        target=self.data/'bad.exe'
        with patch.object(updates.urllib.request,'build_opener',return_value=fake):
            with self.assertRaises(ValueError):updates.download_installer(release,target)
        self.assertFalse(target.exists());self.assertFalse(target.with_suffix('.partial').exists())

    def test_download_redirect_allowlist(self):
        for url in ['http://github.com/setup.exe','https://evil.invalid/setup.exe','https://release-assets.githubusercontent.com:8443/x']:
            with self.assertRaises(ValueError):updates.DownloadRedirects().redirect_request(None,None,302,'',{},url)

    def test_cancelled_installer_reopens_original_calendar(self):
        spec=importlib.util.spec_from_file_location('test_apply_update',ROOT/'apply_update.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        folder=self.data/'updates';folder.mkdir();installer=folder/'setup.exe';installer.write_bytes(b'MZ SAMPLE')
        (self.root/'Sunny Calendar Demo.exe').touch()
        plan={'root':str(self.root),'installer':str(installer),'size':installer.stat().st_size,'sha256':hashlib.sha256(installer.read_bytes()).hexdigest(),'version':'0.3.1','clientPid':1,'serverPid':2}
        with patch.object(runner,'wait_for_exit'),patch.object(runner.subprocess,'run',return_value=type('Result',(),{'returncode':2})()),patch.object(runner.subprocess,'Popen') as reopened:
            runner.run(plan);reopened.assert_called_once()
        self.assertEqual(json.loads((self.data/'last-update.json').read_text())['result'],'not-finished')

if __name__=='__main__':unittest.main()
