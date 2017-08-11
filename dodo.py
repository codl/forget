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
                new.save('static/logotype-{}.png'.format(width))
            im.save('static/logotype.png')

    return {
            'actions': [gen_logo],
            'targets': [f'static/logotype-{width}.png' for width in widths]\
                + ['static/logotype.png'],
            'file_dep': ['assets/logotype.png'],
        }

if __name__ == '__main__':
    import doit
    doit.run(globals())
