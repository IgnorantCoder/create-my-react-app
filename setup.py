import argparse
import subprocess
import os
import shutil
import subprocess
from typing import List, Tuple


def replace_all(line: str, dic: List[Tuple[str, str]]):
    if len(dic) == 0:
        return line
    k, v = dic[0]
    return replace_all(line.replace('%{}%'.format(k), v), dic[1:])


def struct_directory_tree(target: str):
    dirs = ['src']
    for d in dirs:
        os.makedirs(os.path.join(target, d))
    return


def gitignore():
    def copy(target: str):
        shutil.copyfile(
            template('gitignore.template'),
            os.path.join(target, '.gitignore'))
        return

    return copy


def template(file_name: str = None):
    dir_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'templates')
    if file_name:
        file_path = os.path.join(dir_path, file_name)
        if not os.path.exists(file_path):
            raise RuntimeError('Not found {}'.format(file_path))
        return file_path
    return dir_path


def npm(ssr: bool):
    def prepare_npm(target: str):
        def install(packages: List[str], dev: bool = False):
            opt = '--save-dev' if dev else '--save'
            cmd = ['npm', 'install', opt] + packages
            proc = subprocess.Popen(cmd, cwd=target)
            proc.wait()
            return

        dev_packages = [
            'webpack',
            'webpack-cli',
            'webpack-node-externals',
            'typescript',
            'ts-loader',
            'tslint',
            'tslint-loader',
            'tslint-config-airbnb',
            'jest',
            'ts-jest',
            'enzyme',
            'enzyme-adapter-react-16',
            'react-test-renderer',
            '@storybook/cli@alpha',
            '@storybook/react@alpha',
            '@storybook/addon-actions@alpha',
            '@storybook/addon-knobs@alpha',
            '@storybook/addon-options@alpha',
        ]

        lib_packages = [
            "md5",
            "react",
            "react-dom",
            "react-redux",
            "react-router",
            "react-router-dom",
            "react-router-redux@next",
            "recompose",
            "redux",
            "styled-components",
        ]

        types_packages = [
            "@types/enzyme",
            "@types/enzyme-adapter-react-16",
            "@types/jest",
            "@types/md5",
            "@types/react",
            "@types/react-dom",
            "@types/react-redux",
            "@types/react-router",
            "@types/react-router-dom",
            "@types/react-router-redux",
            "@types/react-test-renderer",
            "@types/recompose",
            "@types/storybook__addon-actions",
            "@types/storybook__addon-knobs",
            "@types/storybook__addon-options",
            "@types/storybook__react",
        ]

        if ssr:
            lib_packages.append('express')
            types_packages.append("@types/express")

        shutil.copyfile(
            template('package.template.json'),
            os.path.join(target, 'package.json'))
        install(lib_packages)
        install(dev_packages, dev=True)
        install(types_packages, dev=True)

        return
    return prepare_npm


def webpack(ssr: bool):
    def config_creator(target: str, suffix: str):
        template_path = template('webpack.config.{}.template'.format(suffix))
        with open(template_path, 'r') as ifs:
            template_data = ifs.readlines()

        def create(dev: bool):
            dictionary = [
                ('BUILD_MODE', 'development'),
                ('TSCONFIG_FILE', 'tsconfig.{}.dev.json'.format(suffix)),
                ('IN_DEVELOPMENT_FLAG', 'true'),
                ('ADDITIONAL', ',\ndevtool: \'inline-source-map\''),
            ] if dev else [
                ('BUILD_MODE', 'production'),
                ('TSCONFIG_FILE', 'tsconfig.{}.prod.json'.format(suffix)),
                ('IN_DEVELOPMENT_FLAG', 'false'),
                ('ADDITIONAL', ''),
            ]
            file_name = 'webpack.config.{}.{}.js'.format(
                suffix,
                'dev' if dev else 'prod')
            with open(os.path.join(target, file_name), 'w') as ofs:
                for line in template_data:
                    modified = replace_all(line, dictionary)
                    ofs.write(modified)
            return
        return create

    def create_all(target: str):
        shutil.copyfile(
            template('webpack.config.preview.template'),
            os.path.join(target, 'webpack.config.preview.js'))

        for_client = config_creator(target, 'client')
        for_client(dev=True)
        for_client(dev=False)
        if ssr:
            for_server = config_creator(target, 'server')
            for_server(dev=True)
            for_server(dev=False)

    return create_all


def typescript(ssr: bool):
    def config_creator(target: str, dev: bool):
        mode = 'dev' if dev else 'prod'
        template_file_name = 'tsconfig.{}.template'.format(mode)
        template_path = template(template_file_name)
        with open(template_path, 'r') as ifs:
            template_data = ifs.readlines()

        def create(client: bool):
            this_suffix = 'client' if client else 'server'
            other_suffix = 'server' if client else 'client'

            dictionary = [
                ('THIS_SIDE', this_suffix),
                ('OTHER_SIDE', other_suffix),
            ]
            file_name = 'tsconfig.{}.{}.json'.format(
                this_suffix,
                'dev' if dev else 'prod')
            with open(os.path.join(target, file_name), 'w') as ofs:
                for line in template_data:
                    modified = replace_all(line, dictionary)
                    ofs.write(modified)
            return
        return create

    def create_all(target: str):
        shutil.copyfile(
            template('tslint.template.json'),
            os.path.join(target, 'tslint.json'))

        for_dev = config_creator(target, dev=True)
        for_prod = config_creator(target, dev=False)
        for_dev(client=True)
        for_prod(client=True)
        if ssr:
            for_dev(client=False)
            for_prod(client=False)
        return

    return create_all


def main():
    parser = argparse.ArgumentParser(
        description='Create react application boilerplate.')
    parser.add_argument('--target',
                        dest='target',
                        type=str,
                        required=True,
                        help='Target directory. Make dir before launch me.')
    parser.add_argument('--ssr',
                        dest='is_ssr',
                        action='store_true',
                        help='Server side rendering or not.')
    args = parser.parse_args()

    target_dir = args.target
    is_ssr = args.is_ssr
    if not os.path.exists:
        raise RuntimeError('Please make target dir before launch me.')

    operations = [
        struct_directory_tree,
        gitignore(),
        npm(is_ssr),
        webpack(is_ssr),
        typescript(is_ssr),
    ]
    for operation in operations:
        operation(target_dir)

    return


if __name__ == '__main__':
    main()
