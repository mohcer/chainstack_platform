"""
Problem Domain:

User Controller handles all the requests to fetch user related details
"""
from flask_restplus import Resource
from flask import request
from ..util.dto import UserDto
from ..exceptions import UserNotFound
from ..service.user_service import *
from ..util.decorator import login_required, admin_required
from flask import current_app
api = UserDto.api
parser_one = api.parser()
parser_two = api.parser()
user_req_data = UserDto.user_req_model
user_res_data = UserDto.user_res_model

parser_one.add_argument('new_user_quota', required=True, location='args')
parser_two.add_argument('Authorization', required=True, help="Valid Auth token is required", location='headers')

@api.route('/')
class ListAndCreateUser(Resource):

    @api.doc('list of all platform registered users')
    @login_required
    @admin_required
    @api.expect(parser_two)
    @api.marshal_list_with(user_res_data, envelope='data')
    def get(self, user_data=None, *args, **kwargs):
        """
        :purpose: Fetches the details of all the platform users.

        Note:
        * Login Required
        * Only Platform Admin is allowed to access the details of all the platform users
        """
        try:
            current_app.logger.info("Request to fetch user details")

            res = get_all_platform_users()
            resp_obj = dict()
            resp_obj['status'] = 'success'
            resp_obj['data'] = res
            if not res:
                resp_obj['message'] = 'currently no users exists on this platform'

        except Exception as e:
            resp_obj = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_obj, 400
        else:
            return resp_obj, 200

    @login_required
    @admin_required
    @api.expect(user_req_data, parser_two, validate=True)
    @api.response(201, 'user created successfully!')
    def post(self, user_data=None, *args, **kwargs):
        """
        :purpose: creates a new platform user

        Note:
        * Login Required
        * Only Platform Admin can create new users on this platform
        """
        try:
            req_data = request.json

            create_new_user(req_data)

            resp_obj = {
                'status': 'success',
                'message': 'user created successfully!'
            }
        except UserAlreadyExists as e:
            resp_obj = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_obj, 409
        except Exception as e:
            resp_obj = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_obj, 400
        else:
            return resp_obj


@api.route('/<user_id>')
@api.doc(params={'user_id': 'user id'})
class User(Resource):
    @api.doc('list user info')
    @login_required
    @admin_required
    @api.expect(parser_two)
    @api.marshal_with(user_res_data)
    def get(self, user_id, user_data=None, *args, **kwargs):
        """
        :purpose: Fetches the details of this user

        Note:
        * Login Required
        * Users are not allowed to access the information of other platform users
        * Platform Admin can access the information of any user
        """
        try:
            user = get_user_by_id(user_id)

            resp_obj = dict()
            resp_obj['status'] = 'success'
            resp_obj['message'] = 'User Found'
            resp_obj['data'] = user
        except UserNotFound as e:
            resp_obj = dict()
            resp_obj['status'] = 'fail'
            resp_obj['message'] = str(e)

            return resp_obj, 404
        except Exception as e:
            resp_obj = dict()
            resp_obj['status'] = 'fail'
            resp_obj['message'] = str(e)

            return resp_obj, 400
        else:
            return resp_obj, 200

    @api.doc('Delete user from this platform')
    @login_required
    @admin_required
    @api.marshal_with(user_res_data)
    def delete(self, user_id, user_data=None, *args, **kwargs):
        """
        :purpose: delete user from this platform

        Note:
        * Login required
        * Only platform admin can delete users from this account
        * Also All the resources created by this user will be automatically deleted
        * Platform Admin cannot delete his own account
        """
        try:
            # check if the given user_id already exists on this platform
            get_user_by_id(user_id)

            delete_platform_user(user_id)

            resp_obj = {
                'status': 'success',
                'message': 'user successfully deleted from this platform'
            }

            return resp_obj
        except UserNotFound as e:
            resp_obj = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_obj
        except Exception as e:
            resp_obj = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_obj

    @api.doc('Set new user resource quota')
    @login_required
    @admin_required
    @api.expect(parser_one, parser_two, validate=True)
    def put(self, user_id, user_data=None, *args, **kwargs):
        """
        :purpose: sets new quota for the given user

        :Note
        * Login required
        * Only platform admin can set/unset new user resource quota
        * any other user cannot create and or set quota for himself or any other platform user
        """
        try:
            args = parser_one.parse_args()
            new_user_quota = args['new_user_quota']

            # check if user exists
            user = get_user_by_id(user_id)

            set_new_user_quota(user, new_user_quota)

            resp_json = {
                'status': 'success',
                'message': 'User Quota updated successfully!'
            }

            return resp_json, 200
        except UserNotFound as e:
            resp_json = {
                'status': 'fail',
                'message': str(e) + 'please create this user first!'
            }

            return resp_json, 404
        except Exception as e:
            resp_json = {
                'status': 'fail',
                'message': str(e)
            }

            return resp_json, 400