from doit import create_after
from glob import glob
from itertools import chain


def reltouch(source_filename, dest_filename):
    from os import stat, utime
    stat_res = stat(source_filename)
    utime(dest_filename, ns=(stat_res.st_atime_ns, stat_res.st_mtime_ns))


def resize_image(basename, width, image_format):
    from PIL import Image
    with Image.open('assets/{}.png'.format(basename)) as im:
        if 'A' in im.getbands() and image_format != 'jpeg':
            im = im.convert('RGBA')
        else:
            im = im.convert('RGB')
        height = im.height * width // im.width
        new = im.resize((width, height), resample=Image.LANCZOS)
        if image_format == 'jpeg':
            kwargs = dict(
                    optimize=True,
                    progressive=True,
                    quality=80,
                    )
        elif image_format == 'webp':
            kwargs = dict(
                    quality=79,
                    )
        elif image_format == 'png':
            kwargs = dict(
                    optimize=True,
                    )
        new.save('static/{}-{}.{}'.format(basename, width, image_format),
                 **kwargs)
        reltouch('assets/{}.png'.format(basename),
                 'static/{}-{}.{}'.format(basename, width, image_format))


def task_logotype():
    """resize and convert logotype"""
    widths = (200, 400, 600, 800)
    image_formats = ('jpeg', 'webp')
    for width in widths:
        for image_format in image_formats:
            yield dict(
                    name='{}.{}'.format(width, image_format),
                    actions=[(resize_image,
                              ('logotype', width, image_format))],
                    targets=[f'static/logotype-{width}.{image_format}'],
                    file_dep=['assets/logotype.png'],
                    clean=True,
                )


def task_service_icon():
    """resize and convert service icons"""
    widths = (20, 40, 80)
    formats = ('webp', 'png')
    for width in widths:
        for image_format in formats:
            for basename in ('twitter', 'mastodon'):
                yield dict(
                    name='{}-{}.{}'.format(basename, width, image_format),
                    actions=[(resize_image, (basename, width, image_format))],
                    targets=[
                        'static/{}-{}.{}'.format(basename, width,
                                                 image_format)],
                    file_dep=['assets/{}.png'.format(basename)],
                    clean=True,
                )


def task_copy():
    "copy assets verbatim"

    assets = ('icon.png', 'logotype.png')

    def do_the_thing(src, dst):
        from shutil import copy
        copy(src, dst)
        reltouch(src, dst)

    for asset in assets:
        src = 'assets/{}'.format(asset)
        dst = 'static/{}'.format(asset)
        yield dict(
                name=asset,
                actions=[(do_the_thing, (src, dst))],
                targets=[dst],
                file_dep=[src],
                clean=True,
            )


def task_minify_css():
    """minify css file with csscompressor"""

    from csscompressor import compress

    def minify():
        with open('assets/styles.css') as in_:
            with open('static/styles.css', 'w') as out:
                out.write(compress(in_.read()))
        reltouch('assets/styles.css', 'static/styles.css')

    return dict(
            actions=[minify],
            targets=['static/styles.css'],
            file_dep=['assets/styles.css'],
            clean=True,
        )


def task_rollup():
    """rollup javascript bundle"""

    filenames = ['settings.js', 'instance_buttons.js']
    for filename in filenames:
        src = 'assets/{}'.format(filename)
        dst = 'static/{}'.format(filename)
        name = filename.split('.')[0]
        yield dict(
                name=filename,
                file_dep=list(chain(
                    # fuck it
                    glob('assets/*.js'),
                    glob('components/*.html'))) + ['rollup.config.js'],
                targets=[dst],
                clean=True,
                actions=[
                    ['node_modules/.bin/rollup', '-c',
                     '-i', src, '-o', dst, '-n', name, '-f', 'iife'],
                ],
            )


@create_after('logotype')
@create_after('service_icon')
@create_after('copy')
@create_after('minify_css')
@create_after('rollup')
def task_compress():
    """
    make gzip and brotli compressed versions of each
    static file for the server to lazily serve
    """

    files = chain(
            glob('static/*.css'),
            glob('static/*.js'),
            glob('static/*.jpeg'),
            glob('static/*.png'),
            glob('static/*.webp'),
            )

    def compress_brotli(filename):
        import brotli
        with open(filename, 'rb') as in_:
            with open(filename + '.br', 'wb') as out:
                out.write(brotli.compress(in_.read()))
        reltouch(filename, filename+'.br')

    def compress_gzip(filename):
        import gzip
        with open(filename, 'rb') as in_:
            with gzip.open(filename + '.gz', 'wb') as out:
                out.write(in_.read())
        reltouch(filename, filename+'.gz')

    for filename in files:
        yield dict(
                file_dep=(filename,),
                targets=(filename+'.br',),
                name=filename+'.br',
                actions=[(compress_brotli, (filename,))],
                clean=True,
            )
        yield dict(
                file_dep=(filename,),
                targets=(filename+'.gz',),
                name=filename+'.gz',
                actions=[(compress_gzip, (filename,))],
                clean=True,
            )


if __name__ == '__main__':
    import doit
    doit.run(globals())
