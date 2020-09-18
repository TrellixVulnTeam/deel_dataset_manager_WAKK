# -*- encoding: utf-8 -*-

import argparse
import sys

from . import load as load_dataset
from .settings import (
    read_settings,
    get_default_settings,
    get_default_settings_for_local,
)
from .providers.local_provider import LocalProvider
from .providers.remote_provider import RemoteProvider
from .providers.exceptions import DatasetNotFoundError, DatasetVersionNotFoundError


def _store_dataset(args: argparse.Namespace, settings, conf_name):
    """
    Download dataset and store it.
    Args:
        args: Arguments from the command line.
        settings : settings from config
    """
    for dataset in args.datasets:
        print("Fetching {}... ".format(dataset))

        # Split name:version:
        parts = dataset.split(":")
        if len(parts) == 1:
            parts += ["latest"]
        name, version = parts

        # Download the dataset:
        path = load_dataset(
            name,
            mode="path",
            version=version,
            settings=settings,
            force_update=args.force,
        )

        print(
            "Dataset {} loaded from {} and stored at '{}'.".format(
                dataset, conf_name, path
            )
        )


def _list_dataset_for_provider(provider):
    """
    List all datasets available on provider.

    Args:
        provider: provider object
    """

    location = ""
    if isinstance(provider, RemoteProvider):
        if args.local:
            provider = provider.local_provider()
            location = str(provider.root_folder)
        else:
            location = provider.remote_url
    elif isinstance(provider, LocalProvider):
        location = str(provider.root_folder)

    print("Listing datasets at {}:".format(location))

    # List datasets:
    datasets = sorted(provider.list_datasets())
    for dataset in datasets:
        versions = sorted(provider.list_versions(dataset), reverse=True)
        latest = provider.get_version("latest", versions)
        print(
            "  {}: {}".format(
                dataset,
                ", ".join(v if v != latest else v + " [latest]" for v in versions),
            )
        )


def list_datasets(args: argparse.Namespace):
    """
    List the datasets as specified by `args`.

    Args:
        args: Arguments from the command line.
    """

    if args.config is None:
        settings_list = get_default_settings()
    else:
        settings_list = read_settings(args.config)

    # If provider is specified use it,
    # if not list all datasets from all providers in configuration file.
    if args.prov_conf in settings_list:
        settings_list = {args.prov_conf: settings_list[args.prov_conf]}

    for name, settings in settings_list.items():
        print("=============> settings {}".format(settings))
        try:
            print(
                "======================================================================================="
            )
            print(
                "                            Datasets list of the provider {}                   ".format(
                    name
                )
            )
            print(
                "======================================================================================="
            )
            provider = settings.make_provider()
            print("=============> provider {}".format(provider))
            _list_dataset_for_provider(provider)

        except DatasetVersionNotFoundError as e:
            raise e
        except DatasetNotFoundError as e:
            pass


def download_datasets(args: argparse.Namespace):
    """
    Download the dataset specified by `args`.

    Args:
        args: Arguments from the command line.
    """

    if args.config is None:
        settings_list = get_default_settings()
    else:
        settings_list = read_settings(args.config)

    # If provider is specified use it,
    # if not list all datasets from all providers in configuration file.
    if args.prov_conf in settings_list:
        settings_list = {args.prov_conf: settings_list[args.prov_conf]}

    for name, settings in settings_list.items():
        try:
            _store_dataset(args, settings, name)
            break
        except DatasetNotFoundError:
            print("Dataset not in {}".format(name))
            pass


def remove_datasets(args: argparse.Namespace):
    """
    Remove the dataset specified by `args` (locally).

    Args:
        args: Arguments from the command line.
    """

    # This must be a local provider:
    provider: LocalProvider = get_default_settings_for_local().make_provider()  # type: ignore

    if isinstance(provider, RemoteProvider):
        provider = provider.local_provider()

    datasets = args.datasets
    if args.all:
        datasets = provider.list_datasets()

    for dataset in datasets:

        # Split name:version:
        parts = dataset.split(":")

        if len(parts) > 2:
            print("Invalid dataset selector {}.".format(dataset), file=sys.stderr)

        name = parts[0]

        if name not in provider.list_datasets():
            print(
                "Dataset {} not found at {}.".format(dataset, provider.root_folder),
                file=sys.stderr,
            )
            continue

        versions = provider.list_versions(name)

        if len(parts) == 2:
            # name:version format
            version = parts[1]
            if version not in versions:
                print(
                    "Version {} of dataset {} not found at {}.".format(
                        version, name, provider.root_folder
                    ),
                    file=sys.stderr,
                )
                continue
            versions = [version]

        for version in versions:

            # Find the local folder for the dataset:
            folder = provider.get_folder(name, version)
            print("Removing dataset {} at {}... ".format(dataset, folder))
            provider.del_folder(name, version)


parser = argparse.ArgumentParser(description="DEEL dataset manager")
parser.add_argument(
    "-c",
    "--config",
    type=argparse.FileType("r"),
    help="configuration file to use",
    default=None,
)

subparsers = parser.add_subparsers(help="sub-command help", dest="command")
subparsers.required = True

list_parser = subparsers.add_parser("list", help="list datasets")
list_parser.add_argument(
    "prov_conf",
    type=str,
    nargs="?",
    default="default",
    help="provider in configuration to use",
)
list_parser.add_argument(
    "-l",
    "--local",
    action="store_true",
    help="for a non-local provider (e.g., WebDAV), list only local datasets",
)
list_parser.set_defaults(func=list_datasets)

download_parser = subparsers.add_parser("download", help="download datasets")
download_parser.add_argument(
    "datasets",
    type=str,
    nargs="+",
    help="datasets to download, format name:version with :version being optional",
)
download_parser.add_argument(
    "-p",
    "--provider",
    dest="prov_conf",
    type=str,
    nargs="?",
    default="default",
    help="provider in configuration to use",
)
download_parser.add_argument(
    "-f", "--force", action="store_true", help="force download"
)
download_parser.set_defaults(func=download_datasets)

del_parser = subparsers.add_parser("remove", help="remove local datasets")
del_parser.add_argument(
    "datasets",
    type=str,
    nargs="*",
    help="datasets to remove, format name:version, with :version being optional"
    " (if omitted, remove all versions)",
)
del_parser.add_argument(
    "-a",
    "--all",
    action="store_true",
    help="remove all local datasets",
)
del_parser.set_defaults(func=remove_datasets)

args = parser.parse_args()
args.func(args)
