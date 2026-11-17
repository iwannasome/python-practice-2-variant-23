"""MBT только через HTTP-клиент для файловой версии этапа 2."""

from mbt_machine import MBT_SETTINGS, ApiMachine

TestFileApi = ApiMachine.TestCase
TestFileApi.settings = MBT_SETTINGS
