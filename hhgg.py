import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os


class WeatherDiary:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Diary")
        self.root.geometry("800x600")

        # Инициализация списка для хранения записей
        self.weather_records = []
        self.load_data()  # Загрузка данных из файла при старте
        self.setup_ui()  # Настройка графического интерфейса

    def setup_ui(self):
        """Создает все виджеты и размещает их в окне."""
        # Фрейм для полей ввода и кнопок
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10)

        # --- Поля ввода ---
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, sticky="w")
        self.date_entry = ttk.Entry(input_frame, width=15)
        self.date_entry.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Температура (°C):").grid(row=0, column=2, padx=5, sticky="w")
        self.temp_entry = ttk.Entry(input_frame, width=10)
        self.temp_entry.grid(row=0, column=3, padx=5)

        ttk.Label(input_frame, text="Описание:").grid(row=0, column=4, padx=5, sticky="w")
        self.desc_entry = ttk.Entry(input_frame, width=20)
        self.desc_entry.grid(row=0, column=5, padx=5)

        ttk.Label(input_frame, text="Осадки:").grid(row=0, column=6, padx=5, sticky="w")
        self.precip_combo = ttk.Combobox(
            input_frame,
            values=["Да", "Нет"],
            width=8,
            state="readonly"
        )
        self.precip_combo.grid(row=0, column=7, padx=5)

        # --- Кнопки действий ---
        add_button = ttk.Button(input_frame, text="Добавить запись", command=self.add_record)
        add_button.grid(row=0, column=8, padx=10)

        del_button = ttk.Button(input_frame, text="Удалить запись", command=self.delete_record)
        del_button.grid(row=0, column=9, padx=10)

        # --- Таблица для отображения записей ---
        columns = ("ID", "Дата", "Температура (°C)", "Описание", "Осадки")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Описание":
                self.tree.column(col, width=250)
            elif col == "Дата":
                self.tree.column(col, width=120)
            else:
                self.tree.column(col, width=100)

        self.tree.pack(padx=10, pady=10, fill="both", expand=True)

        # --- Фрейм для фильтрации ---
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(pady=10)

        ttk.Label(filter_frame, text="Фильтр по дате:").grid(row=0, column=0, padx=5)
        self.filter_date_entry = ttk.Entry(filter_frame, width=15)
        self.filter_date_entry.grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Температура выше (°C):").grid(row=0, column=2, padx=5)
        self.min_temp_entry = ttk.Entry(filter_frame, width=10)
        self.min_temp_entry.grid(row=0, column=3, padx=5)

        filter_button = ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filter)
        filter_button.grid(row=0, column=4, padx=5)

        clear_filter_button = ttk.Button(filter_frame, text="Сбросить фильтр", command=self.clear_filter)
        clear_filter_button.grid(row=0, column=5, padx=5)

    def validate_input(self, date_str, temp_str, description):
        """Проверяет корректность введенных пользователем данных."""
        if not description.strip():
            messagebox.showerror("Ошибка", "Описание погоды не может быть пустым")
            return False

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный формат даты (используйте ГГГГ-ММ-ДД)")
            return False

        try:
            float(temp_str)
            if float(temp_str) < -100 or float(temp_str) > 100:  # Дополнительная проверка на реалистичность
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Температура должна быть числом в диапазоне от -100 до 100")
            return False

        return True

    def add_record(self):
        """Обрабатывает добавление новой записи."""
        date_str = self.date_entry.get().strip()
        temp_str = self.temp_entry.get().strip()
        description = self.desc_entry.get().strip()
        precipitation = self.precip_combo.get().strip()

        if not precipitation:
            messagebox.showerror("Ошибка", "Выберите наличие осадков")
            return

        if not self.validate_input(date_str, temp_str, description):
            return

        record = {
            "id": len(self.weather_records) + 1,
            "date": date_str,
            "temperature": float(temp_str),
            "description": description,
            "precipitation": precipitation
        }

        self.weather_records.append(record)
        self.save_data()
        self.refresh_table()
        self.clear_input()

    def clear_input(self):
        """Очищает поля ввода после успешной операции."""
        self.date_entry.delete(0, tk.END)
        self.temp_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.precip_combo.set("")

    def refresh_table(self, data=None):
        """Обновляет содержимое таблицы Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        display_data = data if data is not None else self.weather_records

        for record in display_data:
            self.tree.insert("", "end", values=(
                record["id"],
                record["date"],
                f"{record['temperature']:.1f}",
                record["description"],
                record["precipitation"]
            ))

    def apply_filter(self):
        """Фильтрует записи по дате и/или минимальной температуре."""
        filtered = self.weather_records.copy()

        filter_date = self.filter_date_entry.get().strip()
        if filter_date:
            try:
                datetime.strptime(filter_date, "%Y-%m-%d")
                filtered = [r for r in filtered if r["date"] == filter_date]
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный формат даты для фильтра")
                return

        min_temp_str = self.min_temp_entry.get().strip()
        if min_temp_str:
            try:
                min_temp = float(min_temp_str)
                filtered = [r for r in filtered if r["temperature"] >= min_temp]
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный формат минимальной температуры")
                return

        self.refresh_table(filtered)

    def clear_filter(self):
        """Сбрасывает фильтры и показывает все записи."""
        self.filter_date_entry.delete(0, tk.END)
        self.min_temp_entry.delete(0, tk.END)
        self.refresh_table()  # Важно вызвать метод с круглыми скобками

    def delete_record(self):
        """Удаляет выбранную в таблице запись."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return

        record_id_to_delete = int(self.tree.item(selected_item[0])['values'][0])

        # Поиск и удаление записи из списка по ID
        for i in range(len(self.weather_records)):
            if self.weather_records[i]['id'] == record_id_to_delete:
                del self.weather_records[i]
                break

        # Переназначение ID для сохранения последовательности (необязательно для JSON,
        # но полезно для логики приложения)
        for new_id, record in enumerate(self.weather_records, start=1):
            record['id'] = new_id

        self.save_data()
        self.refresh_table()
        messagebox.showinfo("Успех", "Запись успешно удалена")

    def save_data(self):
        """Сохраняет список записей в файл JSON."""
        try:
            with open("weather_records.json", "w", encoding="utf-8") as f:
                json.dump(self.weather_records, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {e}")

    def load_data(self):
        """Загружает записи из файла JSON при запуске программы."""
        if os.path.exists("weather_records.json"):
            try:
                with open("weather_records.json", "r", encoding="utf-8") as f:
                    self.weather_records = json.load(f)
                    # Проверка целостности данных (например, после ручного редактирования файла)
                    for i in range(len(self.weather_records)):
                        if 'id' not in self.weather_records[i]:
                            self.weather_records[i]['id'] = i + 1
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить данные: {e}")
                self.weather_records = []
        else:
            self.weather_records = []


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDiary(root)
    root.mainloop()