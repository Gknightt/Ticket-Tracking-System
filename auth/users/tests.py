from unittest.mock import patch
from types import SimpleNamespace

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorDict, ErrorList
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail, ValidationError as DRFValidationError

from users.forms import LoginForm
from users.models import User
from users.views.login_views import LoginView


class LoginFormCaptchaTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def _make_request(self, method='get'):
		method = method.lower()
		if method == 'post':
			request = self.factory.post('/users/login/ui/')
		else:
			request = self.factory.get('/users/login/ui/')

		middleware = SessionMiddleware(lambda req: None)
		middleware.process_request(request)
		request.session.save()
		return request

	def test_captcha_hidden_by_default(self):
		request = self._make_request()
		form = LoginForm(request=request)
		self.assertNotIn('captcha', form.fields)

	def test_captcha_visible_when_session_flag_set(self):
		request = self._make_request()
		request.session['force_captcha'] = True
		request.session.save()
		form = LoginForm(request=request)
		self.assertIn('captcha', form.fields)

	def test_captcha_visible_for_user_with_failed_attempts(self):
		user = User.objects.create_user(
			email='locked@example.com',
			username='locked',
			password='StrongPass123'
		)
		user.failed_login_attempts = LoginForm.CAPTCHA_FAILED_ATTEMPT_THRESHOLD
		user.save(update_fields=['failed_login_attempts'])

		request = self._make_request(method='post')
		form = LoginForm(data={'email': user.email}, request=request)
		self.assertIn('captcha', form.fields)

	def test_captcha_visible_when_rate_limit_requires_it(self):
		request = self._make_request()
		rate_limit_state = {'captcha_required': True}
		form = LoginForm(request=request, rate_limit_state=rate_limit_state)
		self.assertIn('captcha', form.fields)

	def test_captcha_skipped_during_otp_flow(self):
		request = self._make_request()
		request.session['otp_email'] = 'user@example.com'
		request.session['force_captcha'] = True
		request.session.save()

		form = LoginForm(request=request)
		self.assertNotIn('captcha', form.fields)


class LoginViewOtpRateLimitTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def _build_request(self):
		request = self.factory.post('/users/login/ui/', data={'email': 'user@example.com'})
		middleware = SessionMiddleware(lambda req: None)
		middleware.process_request(request)
		request.session.save()

		# Attach a messages framework instance so form_invalid can use it
		messages_storage = FallbackStorage(request)
		setattr(request, '_messages', messages_storage)
		return request

	def _make_form(self, error_code):
		error_list = ErrorList([ValidationError('error', code=error_code)])
		errors = ErrorDict({
			'__all__': error_list,
		})
		form = type('MockForm', (), {})()
		form.errors = errors
		form._errors = errors
		form.data = {'email': 'user@example.com'}
		form.non_field_errors = lambda: error_list
		return form

	def test_otp_error_does_not_increment_rate_limit(self):
		request = self._build_request()
		view = LoginView()
		view.setup(request)

		otp_form = self._make_form('otp_invalid')

		with patch('users.views.login_views.record_failed_login_attempt') as mock_record:
			view.form_invalid(otp_form)

		mock_record.assert_called_once()
		self.assertTrue(mock_record.call_args.kwargs['skip_for_otp_error'])

	def test_regular_error_still_increments_rate_limit(self):
		request = self._build_request()
		view = LoginView()
		view.setup(request)

		bad_form = self._make_form('authentication_failed')

		with patch('users.views.login_views.record_failed_login_attempt') as mock_record:
			view.form_invalid(bad_form)

		mock_record.assert_called_once()
		self.assertFalse(mock_record.call_args.kwargs['skip_for_otp_error'])


class LoginViewAuthenticationFlowTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(
			email='auth-flow@example.com',
			username='authflow',
			password='StrongPass123!'
		)

	def _prepare_request(self):
		request = self.factory.post('/users/login/ui/', data={'email': self.user.email})
		middleware = SessionMiddleware(lambda req: None)
		middleware.process_request(request)
		request.session.save()
		storage = FallbackStorage(request)
		setattr(request, '_messages', storage)
		return request

	@patch('users.views.login_views.record_successful_login')
	def test_form_valid_sets_tokens_and_respects_remember_me(self, mock_record_success):
		request = self._prepare_request()
		view = LoginView()
		view.setup(request)

		form = SimpleNamespace(
			cleaned_data={'remember_me': True, 'password': 'StrongPass123!', 'otp_code': ''},
			get_user=lambda: self.user
		)

		with patch('users.views.login_views.CustomTokenObtainPairSerializer') as serializer_cls:
			serializer_instance = serializer_cls.return_value
			serializer_instance.is_valid.return_value = True
			serializer_instance.validated_data = {
				'access': 'access-token',
				'refresh': 'refresh-token'
			}
			serializer_instance.user = self.user

			response = view.form_valid(form)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('system-welcome'))
		self.assertEqual(response.cookies['access_token'].value, 'access-token')
		self.assertEqual(response.cookies['refresh_token'].value, 'refresh-token')
		self.assertEqual(int(response.cookies['access_token']['max-age']), 2592000)
		mock_record_success.assert_called_once_with(request)


class LoginViewTwoFactorPromptTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.rate_limit_patch = patch(
			'users.views.login_views.check_login_rate_limits',
			return_value={'login_allowed': True, 'captcha_required': False}
		)
		self.mock_rate_limit = self.rate_limit_patch.start()
		self.addCleanup(self.rate_limit_patch.stop)
		self.failed_patch = patch('users.views.login_views.record_failed_login_attempt')
		self.failed_patch.start()
		self.addCleanup(self.failed_patch.stop)

	@patch('users.forms.CustomTokenObtainPairSerializer')
	def test_login_prompts_for_otp_when_serializer_requires_it(self, serializer_cls):
		serializer_instance = serializer_cls.return_value
		error_detail = {'non_field_errors': [ErrorDetail('OTP required', code='otp_required')]}
		serializer_instance.is_valid.side_effect = DRFValidationError(detail=error_detail)

		response = self.client.post(reverse('auth_login'), {
			'email': 'twofactor@example.com',
			'password': 'Secret123!'
		})

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'users/login.html')
		self.assertTrue(response.context['two_factor_required'])
		self.assertEqual(self.client.session.get('otp_email'), 'twofactor@example.com')
		self.assertEqual(self.client.session.get('otp_password'), 'Secret123!')


class LoginViewCaptchaRequirementTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	def _prepare_request(self):
		request = self.factory.post('/users/login/ui/', data={'email': 'captcha@example.com'})
		middleware = SessionMiddleware(lambda req: None)
		middleware.process_request(request)
		request.session.save()
		storage = FallbackStorage(request)
		setattr(request, '_messages', storage)
		return request

	def test_captcha_flag_set_when_evaluation_requires_it(self):
		request = self._prepare_request()
		view = LoginView()
		view.setup(request)
		mock_form = SimpleNamespace(data={'email': 'captcha@example.com'})

		with patch('users.views.login_views.LoginForm.should_require_captcha', return_value=True):
			view._evaluate_captcha_requirement(mock_form)

		self.assertTrue(request.session['force_captcha'])
		self.assertEqual(request.session['force_captcha_email'], 'captcha@example.com')


class LoginTemplateContextTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_login_template_includes_expected_links(self):
		response = self.client.get(reverse('auth_login'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'users/login.html')
		self.assertEqual(response.context['page_title'], 'Sign In')
		self.assertEqual(response.context['forgot_password_url'], reverse('forgot-password-ui'))
		self.assertEqual(response.context['register_url'], reverse('user-register'))


class InviteAgentViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.non_admin = User.objects.create_user(
			email='agent@example.com',
			username='agentuser',
			password='StrongPass123!'
		)
		self.superuser = User.objects.create_superuser(
			email='super@example.com',
			username='superuser',
			password='StrongPass123!'
		)

	@patch('users.decorators.get_user_from_jwt_cookie')
	def test_non_admin_redirected_to_profile_settings(self, mock_get_user):
		mock_get_user.return_value = self.non_admin
		response = self.client.get(reverse('invite-agent'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('profile-settings'))

	@patch('users.decorators.get_user_from_jwt_cookie')
	def test_superuser_can_render_invite_template(self, mock_get_user):
		mock_get_user.return_value = self.superuser
		response = self.client.get(reverse('invite-agent'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'admins/invite_agent.html')
		self.assertEqual(response.context['user'], self.superuser)
