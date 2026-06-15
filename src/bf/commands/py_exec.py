import asyncio
import re
import uuid
from dataclasses import dataclass
from typing import Final

import discord
from discord.ext import commands


DOCKER_IMAGE: Final[str] = 'python:3.12-alpine'
TIMEOUT_SECONDS: Final[float] = 5.0
MAX_CODE_CHARS: Final[int] = 6_000
MAX_OUTPUT_CHARS: Final[int] = 3_600

_CODE_BLOCK_RE = re.compile(
    r'^\s*```(?:py|python)?\s*\n(?P<code>.*?)(?:\n```)\s*$',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class PythonRunResult:
    output: str
    exit_code: int | None
    timed_out: bool = False


class PyExec(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _strip_code_block(self, code: str) -> str:
        match = _CODE_BLOCK_RE.match(code)
        if match:
            return match.group('code').strip('\n')
        return code.strip()

    def _discord_code_messages(self, text: str) -> tuple[str, ...]:
        text = text.replace('```', '`\u200b``')

        if not text:
            text = 'No output.'

        chunks: list[str] = []
        max_body_len = 1900

        for i in range(0, len(text), max_body_len):
            body = text[i:i + max_body_len]
            chunks.append(f'```text\n{body}\n```')

        return tuple(chunks)

    async def _docker_rm_force(self, container_name: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            'docker',
            'rm',
            '-f',
            container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()

    async def _run_python_sandboxed(self, raw_code: str) -> PythonRunResult:
        code = self._strip_code_block(raw_code)

        if not code:
            return PythonRunResult('No code provided.', exit_code=None)

        if len(code) > MAX_CODE_CHARS:
            return PythonRunResult(
                f'Code is too long. Maximum is {MAX_CODE_CHARS} characters.',
                exit_code=None,
            )

        container_name = f'discord-python-sandbox-{uuid.uuid4().hex}'

        docker_cmd = [
            'docker',
            'run',
            '--rm',
            '--name',
            container_name,

            # No internet / LAN access.
            '--network',
            'none',

            # Resource limits.
            '--cpus',
            '0.5',
            '--memory',
            '128m',
            '--memory-swap',
            '128m',
            '--pids-limit',
            '64',

            # Filesystem hardening.
            '--read-only',
            '--tmpfs',
            '/tmp:rw,noexec,nosuid,nodev,size=16m',

            # Privilege hardening.
            '--cap-drop',
            'ALL',
            '--security-opt',
            'no-new-privileges',
            '--user',
            '65534:65534',

            # Runtime environment.
            '--workdir',
            '/tmp',
            '--env',
            'PYTHONDONTWRITEBYTECODE=1',
            '--env',
            'PYTHONIOENCODING=utf-8',

            # Avoid slow surprise pulls during command execution.
            '--pull',
            'never',

            # Read user code from stdin.
            '-i',
            DOCKER_IMAGE,
            'python3',
            '-I',
            '-B',
            '-',
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return PythonRunResult(
                'Docker executable was not found. Install Docker on the host running the bot.',
                exit_code=None,
            )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(code.encode('utf-8')),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await self._docker_rm_force(container_name)
            return PythonRunResult(
                f'Execution timed out after {TIMEOUT_SECONDS:.0f} seconds.',
                exit_code=None,
                timed_out=True,
            )

        stdout_text = stdout.decode('utf-8', errors='replace')
        stderr_text = stderr.decode('utf-8', errors='replace')

        parts: list[str] = []

        if stdout_text:
            parts.append(stdout_text.rstrip())

        if stderr_text:
            parts.append(stderr_text.rstrip())

        if parts:
            output = '\n'.join(parts)
        else:
            output = f'Process exited with code {proc.returncode} and no output.'

        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + '\n... output truncated ...'

        return PythonRunResult(output=output, exit_code=proc.returncode)

    async def ex_py(self, code: str) -> tuple[str, ...]:
        result = await self._run_python_sandboxed(code)

        if result.timed_out:
            header = 'Timed out.'
        elif result.exit_code is None:
            header = 'Could not run code.'
        else:
            header = f'Exit code: {result.exit_code}'

        return self._discord_code_messages(f'{header}\n\n{result.output}')

    @commands.command(
        name='py',
        description='Executes Python code.',
    )
    async def py(self, ctx: commands.Context[commands.Bot], *, code: str) -> None:
        async with ctx.typing():
            messages = await self.ex_py(code)

        for msg in messages:
            await ctx.send(msg)

    @discord.app_commands.command(
        name='boing-py',
        description='Executes Python code.',
    )
    @discord.app_commands.describe(
        code='Python code, optionally wrapped in a ```py code block.'
    )
    async def boingpy(self, interaction: discord.Interaction, code: str) -> None:
        await interaction.response.defer(thinking=True)

        messages = await self.ex_py(code)

        await interaction.followup.send(messages[0])
        for msg in messages[1:]:
            await interaction.followup.send(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(PyExec(bot))