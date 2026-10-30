"""Workstation-specific app links, without launching any real app."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('desktop_tools',Path(__file__).resolve().parents[1]/'desktop_tools.py')
tools=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)

class AppLinksTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config=tools.defaults()
        self.env=patch.dict(os.environ,{'SystemDrive':str(self.root),'PROGRAMFILES':str(self.root/'Program Files'),'PROGRAMFILES(X86)':str(self.root/'Program Files (x86)'),'ProgramW6432':str(self.root/'Program Files'),'LOCALAPPDATA':str(self.root/'Local')})
        self.env.start();self.addCleanup(self.env.stop)
        self.registry=patch.object(tools,'registry_app_paths',return_value=[])
        self.registry.start();self.addCleanup(self.registry.stop)

    def make_app(self,relative):
        p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'test-only')
        return p

    def test_new_pos_filename_and_ambiguous_versions(self):
        app=self.make_app('Order/sales(2026.10.30).exe')
        self.assertEqual(tools.resolve_app('pos',self.config),app)
        self.make_app('Order/sales(old).exe')
        self.assertIsNone(tools.resolve_app('pos',self.config))

    def test_32bit_vpn_is_detected(self):
        app=self.make_app('Program Files (x86)/SoftEther VPN Client/vpncmgr.exe')
        self.assertEqual(tools.resolve_app('vpn',self.config),app)

    def test_saved_path_wins_and_missing_path_does_not_open_another_app(self):
        app=self.make_app('Custom location/POS.exe')
        self.config['apps']['pos']['path']=str(app)
        self.assertEqual(tools.resolve_app('pos',self.config),app)
        app.unlink()
        self.make_app('Order/sales.exe')
        self.assertIsNone(tools.resolve_app('pos',self.config))

    def test_old_settings_migrate_without_losing_links_or_folders(self):
        old={'roots':[{'label':'Company','path':r'C:\Shared'}],'links':[{'label':'Docs','target':'https://example.com'}]}
        (self.root/'desktop-tools.json').write_text(json.dumps(old),encoding='utf-8')
        value=tools.read_config(self.root)
        self.assertEqual(value['roots'],old['roots'])
        self.assertEqual(value['links'][0],old['links'][0])
        self.assertEqual(set(value['apps']),{'pos','vpn','obsidian'})

    def test_app_path_rejects_commands_scripts_and_device_paths(self):
        for bad in ['notepad.exe',r'C:\app.cmd',r'C:\app.exe --password secret',r'\\?\C:\app.exe',r'C:\app.exe\nother']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):tools.app_path(bad)
        self.assertEqual(tools.app_path('"C:\\Program Files\\App\\app.exe"'),r'C:\Program Files\App\app.exe')

    def test_settings_persist_locally_and_missing_click_opens_setup(self):
        config=tools.defaults();config['apps']['obsidian']['visible']=False
        tools.save_config(self.root,config)
        self.assertFalse(tools.read_config(self.root)['apps']['obsidian']['visible'])
        with patch.object(tools,'open_desktop_app') as opened:
            self.assertEqual(tools.handle_post('/local-api/tools/open',{'kind':'pos'},self.root),{'opened':False,'needsSetup':'pos'})
            opened.assert_not_called()

    def test_open_uses_saved_target_and_future_app_slot(self):
        app=self.make_app('Different folder/Company app.exe')
        config=tools.defaults();config['apps']['pos']['path']=str(app)
        config['links'][0]={'label':'Future app','target':str(app)}
        tools.save_config(self.root,config)
        with patch.object(tools,'open_desktop_app') as opened:
            self.assertTrue(tools.handle_post('/local-api/tools/open',{'kind':'pos'},self.root)['opened'])
            self.assertEqual(Path(opened.call_args.args[0]),app)
            self.assertTrue(tools.handle_post('/local-api/tools/open',{'kind':'link','index':0},self.root)['opened'])
            self.assertEqual(Path(opened.call_args.args[0]),app)

    def test_picker_returns_selected_file_without_opening_it(self):
        app=self.make_app('Picked app.exe')
        with patch.object(tools,'pick_app_file',return_value=str(app)),patch.object(tools,'open_desktop_app') as opened:
            self.assertEqual(tools.choose_app_file(),{'path':str(app),'cancelled':False})
            opened.assert_not_called()

if __name__=='__main__':unittest.main()
