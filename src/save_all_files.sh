#!/bin/bash

# Рабочая директория — остаётся в app/
patches_dir="patches"
mkdir -p "$patches_dir"  # создать, если не существует

# === Корректное определение следующего номера патча ===
next_patch_number=$(
  find "$patches_dir" -maxdepth 1 -type f -name "patch_*.txt" \
  | sed -E 's/.*patch_([0-9]+)\.txt/\1/' \
  | sed 's/^0*//' | sort -n | tail -1
)
# Если ничего не найдено — установить в 1, иначе инкремент
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

# Функция проверки исключения
is_excluded() {
  local path="$1"
  for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    if [[ "$path" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

# === Сохраняем все подходящие файлы ===
find . -type f -print0 | while IFS= read -r -d '' file; do
  if ! is_excluded "$file"; then
    echo "===== $file =====" >> "$patch_file"
    cat "$file" >> "$patch_file"
    echo -e "\n" >> "$patch_file"
  fi
done

# === Добавляем структуру проекта ===
echo "===== Структура проекта (tree из ../) =====" >> "$patch_file"
if command -v tree >/dev/null 2>&1; then
  tree ../ -I "venv|__pycache__|node_modules|project_structure.txt|patches" >> "$patch_file" 2>/dev/null
else
  echo "[!] Утилита 'tree' не установлена, пропущено." >> "$patch_file"
fi

# === Копируем в буфер, если доступен xclip ===
if command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < "$patch_file"
  echo "📋 Содержимое патча скопировано в буфер"
else
  echo "⚠️ Утилита 'xclip' не найдена, копирование в буфер пропущено"
fi

# === Финальный вывод ===
echo "✅ Сохранено как '$patch_file'"
