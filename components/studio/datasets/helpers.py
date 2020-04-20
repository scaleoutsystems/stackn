

def create_and_fetch_dataset(name, namespace, url, project):
    from urllib.request import urlopen
    from tempfile import NamedTemporaryFile
    from shutil import unpack_archive
    zipurl = 'http://stash.compjour.org/data/1800ssa.zip'
    with urlopen(url) as zipresp, NamedTemporaryFile() as tfile:
        tfile.write(zipresp.read())
        tfile.seek(0)
        unpack_archive(tfile.name, '/tmp/test', format='zip')