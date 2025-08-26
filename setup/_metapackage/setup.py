import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-e-learning",
    description="Meta package for oca-e-learning Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-website_slide_no_index',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
