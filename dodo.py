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
        }

def task_copy_icon():
    import shutil
    return {
            'actions': [lambda: shutil.copy('assets/icon.png', 'static/icon.png')],
            'targets': ['static/icon.png'],
            'file_dep': ['assets/icon.png'],
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
        }

if __name__ == '__main__':
    import doit
    doit.run(globals())
