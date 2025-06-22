# =============================================================================
# LinkedIn Lead Extractor (GUI Version)
#
# Author: AK Nahin
# Website: https://aknahin.com
#
# Description: A graphical user interface for the lead extraction tool.
#              This script uses Tkinter for the GUI and runs the core
#              extraction logic in a separate thread to keep the UI responsive.
# =============================================================================

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import json
from lead_extractor_cli import (
    google_search,
    extract_emails,
    extract_phones,
    save_history,
    load_or_create_config
)
import pandas as pd
from datetime import datetime

class LeadExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LinkedIn Lead Extractor by AK Nahin")
        self.geometry("700x550")

        # Style
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # --- Frames ---
        input_frame = ttk.Frame(self, padding="20")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        log_frame = ttk.Frame(self, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # --- Input Fields ---
        ttk.Label(input_frame, text="Job Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.title_entry = ttk.Entry(input_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.title_entry.insert(0, "realtor")

        ttk.Label(input_frame, text="Area/City:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.area_entry = ttk.Entry(input_frame)
        self.area_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.area_entry.insert(0, "Phoenix")
        
        ttk.Label(input_frame, text="Email Provider:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.provider_entry = ttk.Entry(input_frame)
        self.provider_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.provider_entry.insert(0, "gmail.com")

        ttk.Label(input_frame, text="Number to Extract:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.count_entry = ttk.Entry(input_frame)
        self.count_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        self.count_entry.insert(0, "10")
        
        input_frame.columnconfigure(1, weight=1)

        # --- Log Text Area ---
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, state='disabled')
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # --- Buttons ---
        self.start_button = ttk.Button(button_frame, text="Start Extraction", command=self.start_extraction_thread)
        self.start_button.pack(side=tk.RIGHT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_extraction, state='disabled')
        self.stop_button.pack(side=tk.RIGHT)
        
        self.stop_event = threading.Event()

    def log(self, message):
        """Append a message to the log area in a thread-safe way."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)
        self.update_idletasks()

    def start_extraction_thread(self):
        """Starts the extraction process in a new thread to avoid freezing the GUI."""
        self.stop_event.clear()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        try:
            target_count = int(self.count_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for 'Number to Extract'.")
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            return

        # Pass inputs to the thread
        thread = threading.Thread(
            target=self.run_extraction,
            args=(
                self.title_entry.get(),
                self.area_entry.get(),
                self.provider_entry.get(),
                target_count
            ),
            daemon=True
        )
        thread.start()

    def stop_extraction(self):
        """Signals the extraction thread to stop."""
        self.stop_event.set()
        self.log("🛑 Stop signal sent. Finishing current task...")

    def extraction_finished(self):
        """Re-enables UI elements after extraction is done."""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def run_extraction(self, title_input, area, email_provider, target_count):
        """The core logic that runs in a separate thread."""
        try:
            config = load_or_create_config()
            api_key, cx = config["api_key"], config["cx"]
        except Exception as e:
            self.log(f"Error loading config: {e}. Please configure in CLI first.")
            messagebox.showerror("Configuration Error", "Could not load API keys. Please run `lead_extractor_cli.py` once to configure.")
            self.extraction_finished()
            return
            
        collected = []
        seen_links = set()
        query = f'site:linkedin.com/in/ "{title_input}" "{area}" "{email_provider}"'
        self.log(f"▶️ Starting extraction...")
        self.log(f"   Query: {query}")
        start_index = 1

        while len(collected) < target_count and not self.stop_event.is_set():
            self.log(f"\nSearching... Found {len(collected)}/{target_count} contacts.")
            results = google_search(query, api_key, cx, start_index=start_index)
            if not results:
                self.log("No more Google results found.")
                break

            for item in results:
                if self.stop_event.is_set(): break
                
                link = item.get('link')
                if not link or link in seen_links: continue
                seen_links.add(link)

                name = item.get('title', '').split(' - ')[0].strip()
                snippet = item.get('snippet', '')
                search_text = name + " " + snippet

                emails = extract_emails(search_text)
                phones = extract_phones(search_text)

                if emails:
                    collected.append({
                        "Name": name, "Email": emails[0],
                        "Phone": phones[0] if phones else "N/A", "LinkedIn": link
                    })
                    self.log(f"  -> Found: {name} | {emails[0]}")

                if len(collected) >= target_count: break
            
            start_index += 10

        if collected:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            base_filename = f"{title_input}_{area}_{timestamp}".replace(" ", "_")
            
            df = pd.DataFrame(collected)
            excel_file = base_filename + ".xlsx"
            csv_file = base_filename + ".csv"
            
            try:
                df.to_excel(excel_file, index=False)
                df.to_csv(csv_file, index=False)
                self.log(f"\n✅ Success! Saved {len(collected)} contacts to:")
                self.log(f"   - {excel_file}")
                self.log(f"   - {csv_file}")
                messagebox.showinfo("Success", f"Saved {len(collected)} contacts to {excel_file}")
            except Exception as e:
                self.log(f"Error saving files: {e}")
                messagebox.showerror("File Save Error", f"Could not save files. Error: {e}")
                
            save_history({
                "title": title_input, "area": area, "timestamp": timestamp,
                "count": len(collected), "files": [excel_file, csv_file]
            })
        else:
            self.log("\n❌ No data was collected. Try a broader search.")
            messagebox.showwarning("No Results", "No contacts were found with the current criteria.")
            
        self.extraction_finished()


if __name__ == "__main__":
    app = LeadExtractorApp()
    app.mainloop()
