def task_gen_logo():
    """generate versions of the logo in various sizes"""

    from PIL import Image

    widths = (200, 400, 600, 800)

    def gen_logo():
        with Image.open('assets/logotype.png') as im:
            im = im.convert('L')
            for width in widths:
                height = im.height * width // im.width
                new = im.resize((width,height), resample=Image.LANCZOS)
                new.save('static/logotype-{}.png'.format(width), optimize=True)
            im.save('static/logotype.png', optimize=True)

    return {
            'actions': [gen_logo],
            'targets': [f'static/logotype-{width}.png' for width in widths]\
                + ['static/logotype.png'],
            'file_dep': ['assets/logotype.png'],
            'clean': True,
        }

def task_copy_icon():
    import shutil
    return {
            'actions': [lambda: shutil.copy('assets/icon.png', 'static/icon.png')],
            'targets': ['static/icon.png'],
            'file_dep': ['assets/icon.png'],
            'clean': True,
    }

def task_minify_css():
    """minify css"""

    from csscompressor import compress

    def minify():
        with open('assets/styles.css') as in_:
            with open('static/styles.css', 'w') as out:
                out.write(compress(in_.read()))

    return {
            'actions': [minify],
            'targets': ['static/styles.css'],
            'file_dep': ['assets/styles.css'],
            'clean': True,
        }

def task_compress_static():
    import brotli
    import gzip

    deps = ('static/styles.css', 'static/icon.png', 'static/logotype.png') + tuple((f'static/logotype-{width}.png' for width in (200, 400, 600, 800)))
    targets = tuple((f'{file}.br' for file in deps)) + tuple((f'{file}.gz' for file in deps))

    def compress_brotli(dependencies):
        for filename in dependencies:
            with open(filename, 'rb') as in_:
                with open(filename + '.br', 'wb') as out:
                    out.write(brotli.compress(in_.read()))
    def compress_gzip(dependencies):
        for filename in dependencies:
            with open(filename, 'rb') as in_:
                with gzip.open(filename + '.gz', 'wb') as out:
                    out.write(in_.read())

    return dict(
            file_dep=deps,
            targets=targets,
            actions=[compress_brotli, compress_gzip],
            clean=True,
        )

if __name__ == '__main__':
    import doit
    doit.run(globals())
