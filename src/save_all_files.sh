#!/bin/bash

# Рабочая директория — остаётся в app/
patches_dir="patches"
mkdir -p "$patches_dir"  # создать, если не существует

# Определяем следующий номер патча
next_patch_number=$(ls "$patches_dir" | grep -Eo 'patch_[0-9]+' | sed 's/[^0-9]*//g' | sort -n | tail -1)
if [[ -z "$next_patch_number" ]]; then
  next_patch_number=1
else
  next_patch_number=$((next_patch_number + 1))
fi

# Имя нового файла
patch_file=$(printf "%s/patch_%03d.txt" "$patches_dir" "$next_patch_number")
> "$patch_file"  # очистка/создание

# Исключаемые пути
EXCLUDED_PATTERNS=(
  "/__pycache__/"
  "/.pytest_cache/"
  "./save_all_files.sh"
  "./bot.log"
  "./bs4_result.html"
  "./output.txt"
  "./patches/"
)

# Функция проверки на исключение
is_excluded() {
  local path="$1"
  for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    if [[ "$path" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

# Сохраняем все подходящие файлы
find . -type f | while read -r file; do
  if ! is_excluded "$file"; then
    echo "===== $file =====" >> "$patch_file"
    cat "$file" >> "$patch_file"
    echo -e "\n" >> "$patch_file"
  fi
done

# Добавляем дерево проекта
echo "===== Структура проекта (tree из ../) =====" >> "$patch_file"
tree ../ -I "venv|__pycache__|project_structure.txt|node_modules" >> "$patch_file"

# Копируем в буфер
xclip -selection clipboard < "$patch_file"
echo "📋 Содержимое патча скопировано в буфер"

echo "✅ Сохранено как '$patch_file'"
