#!/usr/bin/python
# -*- coding: utf-8 -*-


# Copyright: (c) 2022, DELGEHIER Cedric <cedric.delgehier@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import requests
import os
import datetime
from urlparse import urlparse
import shutil
import tempfile


__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
---
module: sfs
short_description: Upload, download, and delete files in Secure File Service.
description:
  - Upload, download, and delete files in Secure File Service.
version_added: "2.9"

options:

  cert_verify:
    type: bool
    description:
      - Enable TLS verification
    default: False
    aliases: [ verify ]

  context:
    type: str
    description:
      - The context is the folder where the files are stored.
      - This is often the name of the awx project.
    required: false

  local_file_path:
    type: str
    description:
      - Local directory used.
      - With the "put" method, this folder is zipped before the push to SFS.
      - With the "get" method, this folder is used to store the file downloaded.
    default: $PWD/sfs

  org:
    type: str
    description:
      - The organization is the namespace of the contexts.
    required: true

  password:
    type: str
    description:
      - This is the password used to perform the actions.
      - If it is not defined, the module will look for it in the variable "TOWER_PASSWORD"

  remote_file_name:
    type: str
    description:
      - it is the name of the file in the context.
      - With the "put" method, this file will be stored in /{{org}}/{{context}}/
      - If the name is not defined, the file will be pushed with this default value "{{org}}_{{context}}_{{date_epoch}}.zip"

  url:
    type: str
    description:
      - This is the url of the storage service (note this is not necessarily the same as that of the UI)
      - If it is not defined, the module will look for it in the variable "SFS_UPLOAD_URL"
    required: false

  user:
    type: str
    description:
      - This is the user used to perform the actions.
      - If it is not defined, the module will look for it in the variable "TOWER_USERNAME"


author: "Cédric DELGEHIER (@cdelgehier)"
requirements:
  - requests
  - os
  - datetime
  - urlparse
  - shutil
  - tempfile


"""

EXAMPLES = """
- name: "Test sfs"
  hosts: localhost
  gather_facts: false
  vars:
    org: "{{ lookup('env', 'ORG') }}"
    context: "{{ lookup('env', 'CONTEXT') }}"
    remote_file_name: "{{ lookup('env', 'RFILE') }}"

  tasks:
    - name: "List contexts"
      sfs:
        method: list_contexts
        org: "{{ org }}"

    - name: "Delete a file from a context"
      sfs:
        method: delete
        org: "{{ org }}"
        context: "{{ context }}"
        remote_file_name: test.zip

    - name: "List files in a context"
      sfs:
        method: list_files
        org: "{{ org }}"
        context: "{{ context }}"

    - name: "Get a file in a context"
      sfs:
        method: get
        org: "{{ org }}"
        context: "{{ context }}"
        remote_file_name: "{{ remote_file_name }}"
        local_file_path: /tmp

    - name: "Push file to a context"
      sfs:
        org: "{{ org }}"
        context: "{{ context }}"
        local_file_path: /path/to/folder
        # remote_file_name:

    - name: "Return the latest file in a context"
      sfs:
        method: file_most_recent
        org: "{{ org }}"
        context: "{{ context }}"
        # user: myuser
        # password: "my password"
        # url:  secure-file-service.local

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback


def parse_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme, parsed_url.netloc, parsed_url.path


def main():

    argument_spec = dict(
        method=dict(
            type="str",
            default="put",
            choices=[
                "put",
                "get",
                "delete",
                "list_files",
                "file_most_recent",
                "list_contexts",
            ],
        ),
        cert_verify=dict(
            type="bool",
            default=False,
            aliases=["verify"],
        ),
        local_file_path=dict(type="path", required=False),
        remote_file_name=dict(type="str", required=False),
        user=dict(
            type="str",
            fallback=(env_fallback, ["TOWER_USERNAME"]),
        ),
        password=dict(
            type="str",
            no_log=True,
            fallback=(env_fallback, ["TOWER_PASSWORD"]),
        ),
        org=dict(
            type="str",
            required=True,
        ),
        context=dict(
            type="str",
            required=False,
        ),
        url=dict(
            type="str",
            fallback=(env_fallback, ["SFS_UPLOAD_URL"]),
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Extract our parameters
    method = module.params.get("method")
    local_file_path = module.params.get("local_file_path")
    if local_file_path is None:
        local_file_path = "{}/sfs".format(os.getcwd())
    user = module.params.get("user")
    password = module.params.get("password")
    org = module.params.get("org")
    context = module.params.get("context")
    url = module.params.get("url")
    remote_file_name = module.params.get("remote_file_name")
    if remote_file_name is not None and remote_file_name.endswith(".zip"):
        # drop extension .zip
        filetuple = os.path.splitext(remote_file_name)
        remote_file_name = filetuple[0]

    cert_verify = module.params.get("cert_verify")

    if remote_file_name is None:
        date = datetime.datetime.now().strftime("%s")
        remote_file_name = "{}_{}_{}".format(org, context, date)

    # headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    scheme, netloc, path = parse_url(url)
    url = "{}://{}".format(scheme, netloc)

    if method == "put":
        tempdir = tempfile.mkdtemp()
        tempzipfile = os.path.join(tempdir, remote_file_name)
        zipname = "{}.zip".format(tempzipfile)
        headers.pop("Content-Type")
        command = "/files/{}/{}/".format(org, context)

        try:
            shutil.make_archive(tempzipfile, format="zip", root_dir=local_file_path)
        except Exception as e:
            module.fail_json(
                msg="The local file {} cannot be created. {}".format(tempzipfile, e)
            )

        try:
            response = requests.post(
                "{}{}".format(url, command),
                headers=headers,
                auth=(user, password),
                verify=cert_verify,
                data={"name": "uploadFile", "filename": zipname},
                files={"uploadFile": open(zipname, "rb")},
            )
        except Exception as e:
            module.fail_json(
                msg="The local file {} cannot be read. {}".format(tempzipfile, e)
            )
        shutil.rmtree(tempdir)

        if response.ok:
            module.exit_json(
                changed=True,
                response=response.json(),
                code=response.status_code,
            )

        else:
            module.fail_json(
                msg="Something went wrong...",
                response=response.text,
                code=response.status_code,
            )

    if method == "get":
        command = "/files/{}/{}/{}".format(org, context, remote_file_name)

        response = requests.get(
            "{}{}".format(url, command),
            headers=headers,
            auth=(user, password),
            verify=cert_verify,
        )

        if response.ok:
            if not os.path.exists(local_file_path):
                os.mkdir(local_file_path)
            content = response.content
            local_file_fullpath = os.path.join(local_file_path, remote_file_name)
            try:
                with open(local_file_fullpath, "wb") as file:
                    file.write(content)

                module.exit_json(
                    changed=True,
                    code=response.status_code,
                )
            except FileNotFoundError as e:
                module.fail_json(
                    msg="The local file {} can't be created.".format(
                        local_file_fullpath
                    )
                )
        else:
            module.fail_json(
                msg="Something went wrong...",
                response=response.text,
                code=response.status_code,
            )

    if method == "delete":
        command = "/files/{}/{}/{}".format(org, context, remote_file_name)

        response = requests.delete(
            "{}{}".format(url, command),
            headers=headers,
            auth=(user, password),
            verify=cert_verify,
        )

        if response.ok:
            module.exit_json(
                changed=True,
                response=response.json(),
                code=response.status_code,
            )

        else:
            module.fail_json(
                msg="Something went wrong...",
                response=response.text,
                code=response.status_code,
            )

    if method in ["list_files", "file_most_recent"]:
        command = "/files/{}/{}".format(org, context)

        response = requests.get(
            "{}{}".format(url, command),
            headers=headers,
            auth=(user, password),
            verify=cert_verify,
        )

        if response.ok:

            if method == "file_most_recent":
                listing = response.json()["files"]
                latest = max(listing, key=lambda k: k["date"])

                module.exit_json(
                    changed=False,
                    code=response.status_code,
                    file_most_recent=latest,
                )

            module.exit_json(
                changed=False,
                code=response.status_code,
                listing=response.json(),
            )
        else:
            module.fail_json(
                msg="Something went wrong...",
                response=response.text,
                url="{}{}".format(url, command),
                code=response.status_code,
            )

    if method == "list_contexts":
        command = "/contexts"

        response = requests.get(
            "{}{}".format(url, command),
            headers=headers,
            auth=(user, password),
            verify=cert_verify,
        )

        if response.ok:
            module.exit_json(
                changed=False,
                code=response.status_code,
                listing=response.json(),
            )
        else:
            module.fail_json(
                msg="Something went wrong...",
                response=response.text,
                url="{}{}".format(url, command),
                code=response.status_code,
            )


if __name__ == "__main__":
    main()
