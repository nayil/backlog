# Backlog Manager — User Manual

**Version:** v0.2.0
**Release Date:** 2026-03-12

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface Overview](#main-interface-overview)
4. [Features and Usage](#features-and-usage)
   - [Navigating Items](#navigating-items)
   - [Adding an Item](#adding-an-item)
   - [Editing an Item](#editing-an-item)
   - [Deleting an Item](#deleting-an-item)
   - [Toggling Item Status](#toggling-item-status)
   - [Searching and Filtering](#searching-and-filtering)
   - [Trash Bin](#trash-bin)
   - [Restoring Items from Trash](#restoring-items-from-trash)
   - [Permanently Deleting Items](#permanently-deleting-items)
   - [Viewing Help](#viewing-help)
   - [Quitting the Application](#quitting-the-application)
5. [Keyboard Shortcuts Reference](#keyboard-shortcuts-reference)
6. [Trash and Retention Policy](#trash-and-retention-policy)
7. [Known Limitations](#known-limitations)

---

## Introduction

Backlog Manager is a terminal-based task management application built with a text user interface (TUI). It allows you to manage your backlog items — including adding, editing, deleting, filtering, and organizing tasks — entirely from the command line.

Starting from v0.2.0, the application includes the following key features:

- **Add / Edit / Delete items** with interactive forms and confirmation dialogs
- **Status management**: track items through Todo, In Progress, and Done states
- **Search and filter** items by keyword, status, or category
- **Trash bin with 180-day retention**: deleted items are safely stored in a trash bin and can be restored within 180 days
- **Delete confirmation dialogs**: prevent accidental deletions with a two-step confirmation
- **Built-in help screen**: press `?` at any time to view a summary of all keyboard shortcuts and features

---

## Getting Started

Launch the application from the terminal in your project directory:

```bash
python -m src.app
# or
python src/app.py
```

The application opens in your terminal and displays the main item list. No additional configuration is required — the database is created automatically on first launch.

---

## Main Interface Overview

The main screen consists of the following areas:

- **Top bar**: dropdown filters for Status and Category
- **Item list**: the main table displaying all active backlog items (columns: ID, Title, Status, Priority, Category, Created At)
- **Bottom status bar (Footer)**: displays all available keyboard shortcuts for the current screen

> Items in the trash bin are not shown in the main list. Use the Trash view to manage deleted items.

---

## Features and Usage

### Navigating Items

Use the **Up Arrow (↑)** and **Down Arrow (↓)** keys to move the cursor between items in the list.

---

### Adding an Item

Press `a` to open the **Add Item** form.

Fill in the item details:
- **Title** (required)
- **Status**: Todo / In Progress / Done
- **Priority**: Low / Medium / High
- **Category**: a text label to group related items

Press **Enter** or the confirm button to save the item. It will immediately appear in the main list.

---

### Editing an Item

Select an item using the arrow keys, then press `e` to open the **Edit Item** form.

The form is pre-filled with the current item details. Modify any field and confirm to save changes.

---

### Deleting an Item

Select an item and press `d` to delete it.

A **confirmation dialog** will appear showing the item title and the message:
> "Move to Trash? — The item will be moved to trash and can be restored within 180 days."

- Press `y` or `Enter` to confirm and move the item to the Trash.
- Press `n` or `Esc` to cancel and keep the item.

If the delete operation succeeds, a notification "Item moved to trash" is shown. If it fails, "Delete failed" is shown.

> Deleting an item does not permanently remove it. All deleted items go to the Trash and can be recovered within 180 days.

---

### Toggling Item Status

Select an item and press `s` to advance its status through the following cycle:

```
Todo → In Progress → Done → In Progress → Done → ...
```

Note: Once an item reaches **Done**, pressing `s` returns it to **In Progress**. Items in **In Progress** advance to **Done**, not back to **Todo**. To return an item to **Todo**, use the Edit form (`e`).

---

### Searching and Filtering

**Keyword search:**
Press `/` to open the **Search / Filter** dialog. Type a keyword to filter items by title or other text fields. Press `Esc` to clear the filter and return to the full list.

**Status and Category filters:**
Use the dropdown selectors at the top of the main screen to filter items by Status (All / Todo / In Progress / Done) or Category. Selecting a filter updates the list immediately.

---

### Trash Bin

Press `t` to open the **Trash** view.

The Trash screen shows all deleted items that have not yet expired, with the following columns:

| Column | Description |
|--------|-------------|
| ID | Item identifier |
| Title | Item name |
| Category | Item category |
| Deleted At | Date and time when the item was deleted |
| Expires At | Date after which the item will be permanently removed |

Items in the Trash are kept for **180 days** from the time of deletion. After 180 days, they are automatically and permanently removed.

Press `Esc` to close the Trash view and return to the main screen.

---

### Restoring Items from Trash

Inside the **Trash** view, select an item and press `r` to restore it.

The item is moved back to the main list with its original details intact. It will immediately appear in the main item list when you close the Trash view.

---

### Permanently Deleting Items

Inside the **Trash** view, select an item and press `x` to permanently delete it.

A **confirmation dialog** will appear with the message:
> "Delete Forever? — This action cannot be undone."

- Press `y` or `Enter` to confirm permanent deletion. The item is removed from the database and cannot be recovered.
- Press `n` or `Esc` to cancel.

> Permanent deletion is irreversible. Use this with caution.

---

### Viewing Help

Press `?` from the main screen to open the **Help** window.

The Help screen displays a summary of all available keyboard shortcuts and feature descriptions in English. It is available at any time without interrupting your work.

Press `Esc` or `q` to close the Help window and return to the main screen.

> Note: pressing `q` inside the Help window closes only the Help window. It does not quit the application.

---

### Quitting the Application

Press `q` from the **main screen** to quit the application.

---

## Keyboard Shortcuts Reference

### Main Screen

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move cursor between items |
| `a` | Add a new item |
| `e` | Edit selected item |
| `d` | Delete selected item (moves to Trash, with confirmation) |
| `s` | Advance item status: Todo → In Progress → Done → In Progress |
| `/` | Open search / filter by keyword |
| `t` | Open Trash bin |
| `?` | Show keyboard shortcuts and help |
| `q` | Quit the application |

### Trash Screen

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move cursor between trash items |
| `r` | Restore selected item to main list |
| `x` | Permanently delete selected item (with confirmation) |
| `Esc` | Close Trash view and return to main screen |

### Help Screen

| Key | Action |
|-----|--------|
| `Esc` | Close Help window |
| `q` | Close Help window (does not quit the application) |

### Confirmation Dialogs

| Key | Action |
|-----|--------|
| `y` or `Enter` | Confirm the action |
| `n` or `Esc` | Cancel the action |

---

## Trash and Retention Policy

Backlog Manager uses **soft deletion** for all delete operations:

- When you delete an item, it is moved to the Trash rather than being immediately removed from the database.
- Trash items are retained for **180 days** from the time of deletion.
- During this 180-day window, you can restore any item to the main list at any time.
- When the application starts, items that have exceeded their 180-day retention period are automatically and permanently removed.
- The Trash view only shows items that are still within their retention period.

**Summary of deletion behaviors:**

| Action | What Happens | Reversible? |
|--------|-------------|-------------|
| Press `d` on main screen | Item moves to Trash (soft delete) | Yes — restore within 180 days |
| Press `r` in Trash | Item is restored to main list | N/A |
| Press `x` in Trash | Item is permanently deleted | No |
| Automatic purge at startup | Items past 180-day retention are permanently removed | No |

---

## Known Limitations

1. **Local time used for retention calculation**: The 180-day expiry is calculated using the local system time (without timezone information). In environments spanning multiple timezones, there may be slight discrepancies in expiry timing.

2. **Startup cleanup is synchronous**: When the application starts, it synchronously removes all expired trash items. For users with very large trash bins, this may add a brief delay on startup. For typical usage, this is not noticeable.

3. **Help screen content is static**: The help text is embedded in the application. If you are using a customized or modified version of the application, the help screen may not reflect all available commands.

4. **TUI automated testing is limited**: The visual screens (confirmation dialogs, Trash view, Help screen) are verified through code review and manual testing. Automated UI regression tests are not yet implemented for these components.

---

*Backlog Manager v0.2.0 — Released 2026-03-12*
