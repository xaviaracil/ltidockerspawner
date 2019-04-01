import os

from dockerspawner.dockerspawner import DockerSpawner
from ltiauthenticator.lti_aware import LTIAwareMixin
from traitlets import Unicode


class LTIDockerSpawner(DockerSpawner, LTIAwareMixin):
    """
    DockerSpawner that defines notebook_dir and container_image
    from LTI (http://www.imsglobal.org/activity/learning-tools-interoperability) context
    """

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

    notebooks_git_repo_param_name = Unicode(
        os.getenv('LTI_SPAWNER_GIT_REPO_PARAM_NAME'),
        config=True,
        allow_none=True,
        help=("Param name in LTI context defining the git repo where the work is stored. \n"
              "                If not found, container_image is used as default")
    )

    @property
    def container_name(self):
        return "{}-{}".format(super().container_name, self.provider.resource_link_id)

    def _fmt(self, v):
        format_args = dict(
                context_id=self.provider.context_id,
                repo_name='Jupyter',
                codi_tercers=self.provider.get_custom_param("domain_coditercers") # UOC only
        )

        if self.notebooks_git_repo_param_name:
            if self.provider.get_custom_param(self.notebooks_git_repo_param_name):
                format_args['repo_name'] = self.provider.get_custom_param(self.notebooks_git_repo_param_name)

        return v.format(**format_args)

    def get_env(self):
        env = super().get_env()
        if self.notebooks_git_repo:
            git_repo_url = self._fmt(self.notebooks_git_repo)
            self.log.info(
                "notebooks_git_repo present with value %s. Formatted: %s",
                self.notebooks_git_repo, git_repo_url)
            env["NOTEBOOK_GIT_REPO"] = git_repo_url
            env["NOTEBOOK_GIT_DIR"] = self.provider.get_custom_param("domain_coditercers")

        return env

    def start(self, image=None, extra_create_kwargs=None, extra_start_kwargs=None, extra_host_config=None):
        """Get image name from LTI context"""
        if self.container_image_param_name:
            if self.provider.get_custom_param(self.container_image_param_name):
                image = self.provider.get_custom_param(self.container_image_param_name)

        return super().start(image, extra_create_kwargs, extra_start_kwargs, extra_host_config)