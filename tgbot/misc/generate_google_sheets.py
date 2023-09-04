import gspread

from gspread import Client
from gspread_formatting import *


class Sheets:

    def __init__(self):
        self.__gc: Client = gspread.service_account(r'service_accounts/service_account.json')

    def create_sheet(self, email_acc, name):
        """
        Создает таблицу и возвращает ссылку
        :param email_acc: Основной email адрес для клиента при создании
        :param name: Имя таблицы
        :return: ссылка на таблицу
        """
        worksheet = self.__gc.create(name)
        worksheet.share(email_address=email_acc, perm_type='user',
                        role='writer')
        header_row_list = ['5 звёзд', '4 звезды', '3 звезды', '2 звезды', '1 звезда',
                           'Триггеры', 'Рекомендации']
        self.add_worksheet(url=worksheet.url, name_sheet=header_row_list)
        worksheet.del_worksheet(worksheet.get_worksheet(0))
        self.creat_header_values(worksheet)
        self.triggers_header(worksheet)
        self.recommendations_header(worksheet)
        return worksheet.url

    def share_sheet(self, email, url):
        """
        Добавляет доступ к таблице
        :param email: Добавление дополнительного email к таблицам
        :param url: Ссылка на таблицу клиента
        """
        worksheet = self.__gc.open_by_url(url)
        worksheet.share(email, perm_type='user', role='writer')

    def remove_per(self, email_address, url):
        """
        Удаляет доступ у пользователя к таблице
        :param email_address:
        :param url: Ссылка на таблицу клиента
        :return:
        """
        worksheet = self.__gc.open_by_url(url)
        worksheet.remove_permissions(email_address)

    def open_sheet(self, url):
        """
        Открывает таблицу для редактирования
        :param url: Ссылка на таблицу клиента
        :return:
        """
        worksheet = self.__gc.open_by_url(url)
        return worksheet

    def add_worksheet(self, url: str, name_sheet: list[str]):
        """
        Создание нового листа в таблице
        :return:
        """
        ws = self.open_sheet(url)
        for name in name_sheet:
            ws.add_worksheet(title=name, rows=100, cols=20)

    @staticmethod
    def creat_header_values(ws):
        header_row_list = ['Абзац 1', 'Абзац 2', 'Абзац 3', 'Абзац 4', 'Абзац 5',
                           'Абзац 6']

        sheets = ws.worksheets()
        for sheet in sheets[:5]:
            sheet.append_row(header_row_list)
            sheet.format("A1:F1", {
                'textFormat': {
                    'bold': True
                },
                "horizontalAlignment": "CENTER"
            })
            sheet.freeze(rows=1)
            set_column_width(sheet, 'A:F', 110)

    @staticmethod
    def triggers_header(ws):
        sheet = ws.get_worksheet(5)
        row = ['Фраза', 'Ответ (понимает синтаксис)']
        sheet.append_row(row)
        sheet.format("A1:B1", {
            'textFormat': {
                'bold': True
            },
            "horizontalAlignment": "CENTER"
        })
        sheet.freeze(rows=1)
        set_column_width(sheet, 'A:B', 245)

    @staticmethod
    def recommendations_header(ws):
        sheet = ws.get_worksheet(6)
        row = ['Артикул товара 1', 'Для рекомендации', 'Артикул товара 2']
        sheet.append_row(row)
        sheet.format("A1:C1", {
            'textFormat': {
                'bold': True
            },
            "horizontalAlignment": "CENTER"
        })
        sheet.freeze(rows=1)
        set_column_width(sheet, 'A:C', 220)

    def clear_all_sheets(self, url):
        """
        Очищает все листы в таблице
        :param url: Ссылка на таблицу клиента
        """
        ws = self.open_sheet(url)
        worksheets_list = ws.worksheets()
        for work_sheet in worksheets_list:
            work_sheet.clear()

    def clear_sheet(self, url, index_sheet):
        """
        Очищает определенный лист по индексу
        :param url: Ссылка на таблицу клиента
        :param index_sheet: Номер листа в таблице(начинается с 0)
        """
        ws = self.open_sheet(url)
        ws.get_worksheet(index_sheet).clear()
