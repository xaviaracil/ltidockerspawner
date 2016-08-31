import os

from dockerspawner.dockerspawner import DockerSpawner
from ltiauthenticator.lti_aware import LTIAwareMixin
from tornado import gen
from traitlets import Unicode


class LTIDockerSpawner(DockerSpawner, LTIAwareMixin):
    """
    DockerSpawner that defines notebook_dir and container_image
    from LTI (http://www.imsglobal.org/activity/learning-tools-interoperability) context
    """

    notebooks_tar_file = Unicode(
        '',
        config=True,
        allow_none=True,
        help=("Path to a tar file where find notebooks for every context. \n"
              "             If not found, notebook_dir is used as default")
    )

    notebooks_git_repo = Unicode(
        '',
        config=True,
        allow_none=True,
        help="URL of a git repo where find notebooks for every context."
    )

    container_image_param_name = Unicode(
        os.getenv('LTI_SPAWNER_CONTAINER_IMAGE_PARAM_NAME'),
        config=True,
        allow_none=True,
        help=("Param name in LTI context defining the container image to spawn. \n"
              "                If not found, container_image is used as default")
    )

    def _fmt(self, v):
        format_args = dict(
                context_id=self.provider.context_id,
                codi_tercers=self.provider.get_custom_param("domain_coditercers") # UOC only
        )

        return v.format(format_args)

    def get_env(self):
        env = super().get_env()
        if self.notebooks_git_repo:
            git_repo_url = self._fmt(self.notebooks_git_repo)
            self.log.info(
                "notebooks_git_repo present with value %s. Formatted: %s",
                self.notebooks_git_repo, git_repo_url)
            env["NOTEBOOK_GIT_REPO"] = git_repo_url

        return env

    @gen.coroutine
    def start(self, image=None, extra_create_kwargs=None, extra_start_kwargs=None, extra_host_config=None):

        container = yield self.get_container()
        do_copy_notebooks = container is None and self.notebooks_tar_file

        """Get image name from LTI context"""
        if self.container_image_param_name:
            image = self.provider.get_custom_param(self.container_image_param_name)

        """Start the server"""
        yield super().start(image, extra_create_kwargs, extra_start_kwargs, extra_host_config)

        if do_copy_notebooks:
            "Copy notebooks_tar_file to data volume"
            context_tar_file = self._fmt(self.notebooks_tar_file)
            tar_file = open(context_tar_file, "rb")
            tar_data = tar_file.read()
            # build the dictionary of keyword arguments for put_archive
            create_kwargs = dict(
                container=self.container_id,
                path=self.notebook_dir,
                data=tar_data)

            yield self.docker('put_archive', **create_kwargs)
            tar_file.close()