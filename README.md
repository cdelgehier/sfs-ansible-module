[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
# Ansible Collection - cdelgehier.sfs

This collection embeds a module allowing to manage basic actions with a tool like sfss.

## Requirements

The dependencies are:
- requests
- os
- datetime
- urlparse

## Module Variables

If an essential variable is missing, the module will try to look in the execution environment.

To define them just export them in the shell.

```shell
export SFS_UPLOAD_URL='https://secure-file-service.local'
```

```shell
export TOWER_USERNAME='local_user'
```

```shell
export TOWER_PASSWORD='MyP@5sW0RD'
```

## Usage

The use of environment variables greatly simplifies the writing of tasks but it is possible to specify these variables in each task.


### Push a file in a context
```yaml
- name: "Push file to a context"
  sfs:
    org: "{{ org }}"
    context: "{{ context }}"
    local_file_path: /path/to/folder
    # remote_file_name: foo.zip
```

### Delete a file in a context
```yaml
- name: "Delete a file from a context"
  sfs:
    method: delete
    org: "{{ org }}"
    context: "{{ context }}"
    remote_file_name: test.zip
```

### Listing of all contexts for the organization
```yaml
- name: "List contexts"
  sfs:
    method: list_contexts
    org: "{{ org }}"
```

### Listing of all files in a context
```yaml
- name: "List files in a context"
  sfs:
    method: list_files
    org: "{{ org }}"
    context: "{{ context }}"
```

```yaml
- name: "Return the latest file in a context"
  sfs:
    method: file_most_recent
    org: "{{ org }}"
    context: "{{ context }}"
```

### Download a file from a context
```yaml
- name: "Get a file from a context"
  sfs:
    method: get
    org: "{{ org }}"
    context: "{{ context }}"
    remote_file_name: "{{ remote_file_name }}"
    local_file_path: /tmp
```

## Changelog

See changelog.

## License

GNU GENERAL PUBLIC LICENSE v3
