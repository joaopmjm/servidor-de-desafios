import asyncio
from asgiref.sync import sync_to_async
from django.http import Http404
from django.core.files.base import ContentFile
from django.utils.decorators import classonlymethod
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .challenge_controller import test_code_for
from .serializers import FullCodeChallengeSerializer, ShortCodeChallengeSerializer, CodeChallengeSubmissionSerializer
from .models import CodeChallenge, CodeChallengeSubmission, user_challenge_path
from .code_runner import run_tests


class CodeChallengeListView(APIView):
    """
    List all challenges.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        challenges = CodeChallenge.objects.filter(deleted=False, published=True)
        serializer = ShortCodeChallengeSerializer(challenges, many=True)
        return Response(serializer.data)


def get_challenge_or_404(slug):
    try:
        challenge = CodeChallenge.objects.get(slug=slug)
        if not challenge.deleted and challenge.published:
            return challenge
    except CodeChallenge.DoesNotExist:
        pass
    raise Http404(f'There is no challenge with slug {slug}')


class CodeChallengeView(APIView):
    """
    Get challenge.
    """
    permission_classes = (IsAuthenticated,)

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    async def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.

        This code has been adapted to work with async from: https://github.com/encode/django-rest-framework/blob/master/rest_framework/views.py#L485
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            await sync_to_async(self.initial)(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = sync_to_async(self.http_method_not_allowed)

            response = await handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    def sync_get(self, request, slug, format=None):
        challenge = get_challenge_or_404(slug)
        serializer = FullCodeChallengeSerializer(challenge)
        return Response(serializer.data)

    async def get(self, request, slug, format=None):
        return await sync_to_async(self.sync_get)(request, slug, format)

    def create_submission_and_serialize(self, author, challenge, result, code):
        submission = CodeChallengeSubmission.objects.create(author=author, challenge=challenge)
        submission.failures = result.failure_msgs
        submission.stack_traces = result.stack_traces
        submission.stdouts = [
                [{
                    'output': line[0] if len(line) else None,
                    'input': line[1] if len(line) > 1 else None
                } for line in test_case
            ] for test_case in result.stdouts]
        submission.success = result.success
        submission.save()
        submission.code.save(user_challenge_path(submission, ''), ContentFile(code))

        serializer = CodeChallengeSubmissionSerializer(submission)
        return serializer.data

    async def post(self, request, slug, format=None):
        challenge = await sync_to_async(get_challenge_or_404)(slug)
        code = request.data.get('code')
        test_code = await sync_to_async(test_code_for)(challenge)
        result = await run_tests(code, test_code, challenge.function_name)
        data = await sync_to_async(self.create_submission_and_serialize)(request.user, challenge, result, code)
        return Response(data)


class CodeChallengeSubmissionListView(APIView):
    """
    List all submissions.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, slug, format=None):
        submissions = CodeChallengeSubmission.objects.filter(author=request.user, challenge__slug=slug).order_by('-creation_date')
        serializer = CodeChallengeSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class CodeChallengeSubmissionCodeView(APIView):
    """
    Get challenge submission code.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, slug, submission_id, format=None):
        query_args = {
            'id': submission_id,
            'challenge__slug': slug,
        }
        if not request.user.is_superuser:
            query_args['author__id'] = request.user.id
        try:
            submission = CodeChallengeSubmission.objects.get(**query_args)
            return Response({'code': submission.code.read().decode('utf-8')})
        except CodeChallengeSubmission.DoesNotExist:
            raise Http404('This submission does not exist')
