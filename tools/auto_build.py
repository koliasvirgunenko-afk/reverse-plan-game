from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,tarfile,zipfile
R=Path(__file__).resolve().parents[1]
L=R/'logs'; L.mkdir(exist_ok=True)
B=R/'build'; B.mkdir(exist_ok=True)
report={'commit':os.getenv('GITHUB_SHA'),'finished_game':False,'checks':{}}
def status(name,result,detail=''):
    report['checks'][name]={'status':result,'detail':detail}
    (L/'ci-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def run(name,args,marker=None):
    p=subprocess.run(args,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
    (L/(name+'.log')).write_text(p.stdout)
    print(p.stdout,flush=True)
    ok=p.returncode==0 and not re.search(r'SCRIPT ERROR:|Parse Error:|Failed to load',p.stdout)
    if marker: ok=ok and marker in p.stdout
    status(name,'пройдена' if ok else 'не пройдена','exit='+str(p.returncode))
    return ok
def main():
    for name in ['import','tests','export','binary_smoke','six_chapter_playthrough','collision_safety','performance']:
        status(name,'не выполнена')
    if not run('install',[sys.executable,'tools/install_godot.py']): return 2
    g=str(Path.home()/'.cache/reverse-plan-engine/Godot_v4.7.2-stable_linux.x86_64')
    report['engine']=subprocess.check_output([g,'--version'],text=True).strip()
    if not report['engine'].startswith('4.7.2.'): return 2
    if not run('import',[g,'--headless','--editor','--path',str(R),'--import','--quit']): return 3
    if not run('tests',[g,'--headless','--path',str(R),'--script','res://tests/core_tests.gd'],'failed=0'): return 4
    cfg=(R/'project.godot').read_text()
    scene=re.search(r'run/main_scene\s*=\s*"res://([^"\n]+)"',cfg)
    required=['export_presets.cfg','README_RU.md','CREDITS.txt','LICENSE','docs/ASSET_REGISTER.json','docs/TEST_WALKTHROUGH.md']
    missing=[p for p in required if not (R/p).is_file()]
    if not scene or not (R/scene.group(1)).is_file(): missing.append('playable main scene')
    if missing:
        status('release_inputs','не пройдена',', '.join(missing)); return 5
    if not run('scene_smoke',[g,'--headless','--path',str(R),'--quit-after','60']): return 6
    templates=Path.home()/'.local/share/godot/export_templates/4.7.2.stable'
    if not (templates/'linux_release.x86_64').is_file():
        import urllib.request
        archive=B/'templates.tpz'
        urllib.request.urlretrieve('https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_export_templates.tpz',archive)
        with archive.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
        if digest!='f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011':
            status('template_checksum','не пройдена'); return 7
        templates.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for name in ['linux_release.x86_64','linux_debug.x86_64','version.txt']:
                (templates/name).write_bytes(z.read('templates/'+name))
                if name.startswith('linux_'): (templates/name).chmod(0o755)
        archive.unlink()
    target=B/'Linux'; target.mkdir(exist_ok=True)
    binary=target/'ReversePlan.x86_64'
    if not run('export',[g,'--headless','--path',str(R),'--export-release','Linux',str(binary)]): return 8
    if not binary.is_file() or not (target/'ReversePlan.pck').is_file():
        status('export','не пройдена','Executable or PCK absent'); return 8
    binary.chmod(0o755)
    if not run('binary_smoke',[str(binary),'--headless','--quit-after','60']): return 9
    launcher=target/'start.sh'
    launcher.write_text('#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "${BASH_SOURCE[0]}")"\nexec ./ReversePlan.x86_64 "$@"\n')
    launcher.chmod(0o755)
    for name in ['README_RU.md','CREDITS.txt','LICENSE']: shutil.copy2(R/name,target/name)
    (target/'ENGINE_VERSION.txt').write_text(report['engine']+'\n')
    shutil.copy2(L/'ci-status.json',target/'AUTOMATED_QA.json')
    with tarfile.open(B/'ReversePlan_Linux_DEVELOPMENT.tar.gz','w:gz') as z: z.add(target,arcname='ReversePlan')
    with zipfile.ZipFile(B/'ReversePlan_Source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for base,dirs,files in os.walk(R):
            dirs[:]=[d for d in dirs if d not in ['build','logs','__pycache__'] and not d.startswith('.')]
            for name in files:
                if name.startswith('.') or name.endswith(('.tmp','.pyc')): continue
                p=Path(base)/name; z.write(p,str(p.relative_to(R)))
    status('packaging','пройдена','Development artifacts; playthrough NOT verified')
    return 0
if __name__=='__main__':
    try: code=main()
    except Exception as e:
        status('pipeline_exception','не пройдена',str(e)); raise
    raise SystemExit(code)
