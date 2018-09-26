import ckan.plugins as plugins
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from hashlib import md5

HEADER_USERNAME = "sec-username"
HEADER_ROLES = "sec-roles"
HEADER_ORG = "sec-org"
HEADER_EMAIL = "sec-email"
HEADER_FIRSTNAME = "sec-firstname"
HEADER_LASTNAME = "sec-lastname"
HEADER_TEL = "sec-tel"


def auth_function_disabled(context, data_dict=None):
    return {
        'success': False,
        'msg': 'Authentication is disabled on CKAN and is handled by geOrchestra.'
    }


class GeorchestraPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthenticator)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)

    # ignore basic auth actions
    def login(self):
        pass

    def logout(self):
        pass

    def abort(self, status_code, detail, headers, comment):
        pass

    def identify(self):
        """
        Used to determine the currently logged in user
        Will first check if a username is available and act accordingly (get existing user, create new one)
        """
        headers = toolkit.request.headers
        username = headers.get(HEADER_USERNAME)
        if username:
            email = headers.get(HEADER_EMAIL) or 'empty@empty.org'
            emailhash = md5(email.strip().lower().encode('utf8')).hexdigest()
            firstname = headers.get(HEADER_FIRSTNAME) or 'john'
            lastname = headers.get(HEADER_LASTNAME) or 'doe'
            userdict = {'email': email,
                        'name': username,
                        'fullname': firstname + ' ' + lastname,
                        'password': '12345678'}

            # create user if missing
            try:
                toolkit.get_converter('user_name_exists')(
                    username,
                    {'model': model, 'session': model.Session})
            except toolkit.Invalid:
                toolkit.get_action('user_create')(
                    {'model': model, 'session': model.Session, 'user': None, 'ignore_auth': True},
                    userdict)

            userdict['id'] = toolkit.get_converter('convert_user_name_or_id_to_id')(
                username,
                {'model': model, 'session': model.Session})
            user_obj = toolkit.get_action('user_show')(
                {'model': model, 'session': model.Session, 'user': None, 'ignore_auth': True},
                {'id': userdict['id']})

            # update user if necessary
            if user_obj['email_hash'] != emailhash or user_obj['fullname'] != userdict['fullname']:
                toolkit.get_action('user_update')(
                    {'model': model, 'session': model.Session, 'user': None, 'ignore_auth': True},
                    userdict)

            toolkit.c.user = username
        else:
            toolkit.c.user = None

    # override auth functions
    def get_auth_functions(self):
        return {
            'user_create': auth_function_disabled,
            'group_create': auth_function_disabled
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        # toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'georchestra')
