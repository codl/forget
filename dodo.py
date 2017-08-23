def task_gen_logo():
    """generate versions of the logo in various sizes"""

    from PIL import Image

    def resize_logo(width, format):
        with Image.open('assets/logotype.png') as im:
            im = im.convert('RGB')
            height = im.height * width // im.width
            new = im.resize((width,height), resample=Image.LANCZOS)
            if format == 'jpeg':
                kwargs = dict(
                        optimize = True,
                        progressive = True,
                        quality = 80,
                        )
            elif format == 'webp':
                kwargs = dict(
                        quality = 79,
                        )
            new.save('static/logotype-{}.{}'.format(width, format), **kwargs)

    widths = (200, 400, 600, 800)
    formats = ('jpeg', 'webp')
    for width in widths:
        for format in formats:
            yield dict(
                    name='{}.{}'.format(width, format),
                    actions=[(resize_logo, (width, format))],
                    targets=[f'static/logotype-{width}.{format}'],
                    file_dep=['assets/logotype.png'],
                    clean=True,
                )


def task_copy_asset():
    import shutil
    assets = ('icon.png', 'logotype.png', 'settings.js', 'twitter.png', 'mastodon.png')
    for asset in assets:
        yield dict(
                name=asset,
                actions=[(lambda asset: shutil.copy(f'assets/{asset}', f'static/{asset}'), (asset,))],
                targets=[f'static/{asset}'],
                file_dep=[f'assets/{asset}'],
                clean=True,
            )

def task_minify_css():
    """minify css"""

    from csscompressor import compress

    def minify():
        with open('assets/styles.css') as in_:
            with open('static/styles.css', 'w') as out:
                out.write(compress(in_.read()))

    return dict(
            actions=[minify],
            targets=['static/styles.css'],
            file_dep=['assets/styles.css'],
            clean=True,
        )


def cross(a, b):
    for A in a:
        for B in b:
            yield (A, B)

def task_compress_static():
    import brotli
    import gzip

    files = (
        'static/styles.css',
        'static/icon.png',
        'static/logotype.png',
        'static/settings.js',
        'static/twitter.png',
        'static/mastodon.png',
        ) + tuple((f'static/logotype-{width}.{format}' for width, format in cross((200, 400, 600, 800), ('jpeg','webp'))))

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

    for filename in files:
        yield dict(
                file_dep=(filename,),
                targets=(filename+'.br',),
                name=filename+'.br',
                actions=[compress_brotli],
                clean=True,
            )
        yield dict(
                file_dep=(filename,),
                targets=(filename+'.gz',),
                name=filename+'.gz',
                actions=[compress_gzip],
                clean=True,
            )

if __name__ == '__main__':
    import doit
    doit.run(globals())
