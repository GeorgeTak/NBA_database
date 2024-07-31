import numpy as np
import pandas as pd
import openpyxl
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from nba_api.stats.endpoints import commonteamroster, playercareerstats, scoreboard
from nba_api.stats.static import teams


def get_teams():
    try:
        nba_teams = teams.get_teams()
        return nba_teams
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching teams: {e}")
        return []


def get_team_roster(team_id):
    try:
        team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        roster_data = team_roster.get_data_frames()[0]
        return roster_data
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching team roster: {e}")
        return pd.DataFrame()


def get_player_stats(player_id):
    try:
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats_data = career_stats.get_data_frames()[0]
        return stats_data
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching player stats: {e}")
        return pd.DataFrame()


def get_game_scores(date):
    try:
        game_scores = scoreboard.Scoreboard(game_date=date)
        games = game_scores.get_data_frames()[0]
        return games
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Error fetching game scores: {e}")
        return pd.DataFrame()


def save_stats_to_excel(df, filename):
    try:
        df.to_excel(filename, index=False)
        messagebox.showinfo("Success", f"Stats saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Error saving to Excel: {e}")


def show_team_roster():
    team_id = team_id_entry.get()
    if not team_id.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid team ID.")
        return

    team_id = int(team_id)
    roster = get_team_roster(team_id)

    if not roster.empty:
        roster_text = roster[['PLAYER_ID', 'PLAYER', 'POSITION', 'HEIGHT', 'WEIGHT']].to_string(index=False)
        if 'COLLEGE' in roster.columns:
            roster_text += "\n" + roster[['COLLEGE']].to_string(index=False)
        if 'COUNTRY' in roster.columns:
            roster_text += "\n" + roster[['COUNTRY']].to_string(index=False)

        roster_text_box.config(state=tk.NORMAL)
        roster_text_box.delete(1.0, tk.END)
        roster_text_box.insert(tk.END, roster_text)
        roster_text_box.config(state=tk.DISABLED)
    else:
        messagebox.showinfo("No Data", "No roster data found for the selected team.")


def show_player_stats():
    player_id = player_id_entry.get()
    if not player_id.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid player ID.")
        return

    player_id = int(player_id)
    player_stats = get_player_stats(player_id)

    if not player_stats.empty:
        stats_text = player_stats[
            ['SEASON_ID', 'TEAM_ABBREVIATION', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK']].to_string(index=False)
        player_stats_text_box.config(state=tk.NORMAL)
        player_stats_text_box.delete(1.0, tk.END)
        player_stats_text_box.insert(tk.END, stats_text)
        player_stats_text_box.config(state=tk.DISABLED)

        global stats_df  # Update global variable
        stats_df = player_stats
    else:
        messagebox.showinfo("No Data", "No career stats found for the selected player.")


def show_teams():
    nba_teams = get_teams()
    if nba_teams:
        teams_text = "\n".join([f"ID: {team['id']} - {team['full_name']}" for team in nba_teams])
        teams_text_box.config(state=tk.NORMAL)
        teams_text_box.delete(1.0, tk.END)
        teams_text_box.insert(tk.END, teams_text)
        teams_text_box.config(state=tk.DISABLED)
    else:
        messagebox.showinfo("No Data", "No teams found.")


def save_player_stats():
    if stats_df is not None:
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")],
                                                 initialfile=f"player_{player_id_entry.get()}_career_stats.xlsx")
        if file_path:
            save_stats_to_excel(stats_df, file_path)
    else:
        messagebox.showerror("No Data", "No player stats available to save.")


def predict_player_stats(player_id):
    # Fetch player's last 3 seasons stats
    stats_df = get_player_stats(player_id)
    if stats_df.empty:
        return pd.DataFrame()

    # Filter the last 3 seasons
    last_3_seasons = stats_df.tail(3)

    # Calculate the mean for the required stats
    prediction = {
        'PTS': last_3_seasons['PTS'].mean().round(1),
        'REB': last_3_seasons['REB'].mean().round(1),
        'AST': last_3_seasons['AST'].mean().round(1),
        'BLK': last_3_seasons['BLK'].mean().round(1),
        'STL': last_3_seasons['STL'].mean().round(1),
        'FG%': (last_3_seasons['FG_PCT'] * 100).mean().round(1),
        '3PT%': (last_3_seasons['FG3_PCT'] * 100).mean().round(1)
    }

    for stat, entry in predicted_stats_entries.items():
        entry.configure(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, str(prediction[stat]))
        entry.configure(state='readonly')



def convert_height_to_inches(height):
    if '-' in height:
        feet, inches = height.split('-')
        return int(feet) * 12 + int(inches)
    return 0



def sort_roster(sort_by):
    team_id = team_id_entry.get()
    if not team_id.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid team ID.")
        return

    team_id = int(team_id)
    roster = get_team_roster(team_id)

    if roster.empty:
        messagebox.showinfo("No Data", "No roster data found for the selected team.")
        return

    # Check if the column to sort by exists
    if sort_by not in roster.columns:
        messagebox.showerror("Invalid Column", f"Cannot sort by {sort_by}.")
        return

    # Convert height to inches if sorting by height
    if sort_by == 'HEIGHT':
        roster['HEIGHT_IN_INCHES'] = roster['HEIGHT'].apply(convert_height_to_inches)
        sort_by = 'HEIGHT_IN_INCHES'

    # Sort roster data
    sorted_roster = roster.sort_values(by=sort_by, ascending=False)
    roster_text = sorted_roster[['PLAYER_ID', 'PLAYER', 'POSITION', 'HEIGHT', 'WEIGHT']].to_string(index=False)

    if 'COLLEGE' in sorted_roster.columns:
        roster_text += "\n" + sorted_roster[['COLLEGE']].to_string(index=False)
    if 'COUNTRY' in sorted_roster.columns:
        roster_text += "\n" + sorted_roster[['COUNTRY']].to_string(index=False)

    roster_text_box.config(state=tk.NORMAL)
    roster_text_box.delete(1.0, tk.END)
    roster_text_box.insert(tk.END, roster_text)
    roster_text_box.config(state=tk.DISABLED)



def clear_screen():
    # Hide all frames
    team_frame.grid_forget()
    teams_frame.grid_forget()
    player_frame.grid_forget()
    predicted_stats_frame.grid_forget()
    start_screen_frame.grid_forget()


def show_frame(frame_name):
    # Hide all frames
    clear_screen()

    # Show the desired frame
    if frame_name == "teams":
        teams_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
    elif frame_name == "team":
        team_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
    elif frame_name == "player":
        player_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
    elif frame_name == "predicted_stats":
        predicted_stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')


def show_teams_frame():
    clear_screen()
    show_frame("teams")


def show_team_frame():
    clear_screen()
    show_frame("team")


def show_player_frame():
    clear_screen()
    show_frame("player")


def show_predicted_stats_frame():
    clear_screen()
    show_frame("predicted_stats")


def back_to_teams_frame():
    show_teams_frame()


def back_to_players_frame():
    show_player_frame()


def back_to_team_frame():
    show_team_frame()


# Function to show the start screen
def show_start_screen():
    clear_screen()
    start_screen_frame.grid()


def exit_program():
    root.destroy()


# Create the main window
root = tk.Tk()
root.title("NBA Stats Viewer")
root.configure(background='light blue')
root.geometry("850x400")  # Set a fixed window size

stats_df = None  # Initialize global variable for storing player stats

# Styling
style = ttk.Style()
style.configure('TButton', padding=8, relief='flat', background='#007bff', foreground='#40E0D0', font=('Arial', 12, 'bold'))
style.configure('TLabel', font=('Arial', 12), background="#D3D3D3")
style.configure('TEntry', padding=5)
style.configure('TFrame', background="#ff6f61")
style.configure('TScrolledText', background="#D3D3D3", padding=10)
style.configure('Header.TLabel', foreground='white', background='blue', font=('Arial', 10, 'bold'))

# Teams section (right side)
teams_frame = ttk.Frame(root, padding="10", style='TFrame')
teams_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

show_teams_button = ttk.Button(teams_frame, text="Show All Teams", command=show_teams)
show_teams_button.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

teams_text_box = scrolledtext.ScrolledText(teams_frame, width=50, height=15, state=tk.DISABLED)
teams_text_box.grid(row=1, column=0, padx=5, pady=5, sticky='ew')

# In the teams_frame
next_to_team_button = ttk.Button(teams_frame, text="Next", command=show_team_frame)
next_to_team_button.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

back_to_start_screen = ttk.Button(teams_frame, text="Back", command=show_start_screen)
back_to_start_screen.grid(row=2, column=0, padx=5, pady=5, sticky='ew')

# Team section (left side)
team_frame = ttk.Frame(root, padding="10", style='TFrame')
team_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

team_label = ttk.Label(team_frame, text="Team ID:")
team_label.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

team_id_entry = ttk.Entry(team_frame, width=15)
team_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

show_roster_button = ttk.Button(team_frame, text="Show Team Roster", command=show_team_roster)
show_roster_button.grid(row=0, column=2, padx=5, pady=5, sticky='ew')

roster_text_box = scrolledtext.ScrolledText(team_frame, width=80, height=10, state=tk.DISABLED)
roster_text_box.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

next_to_player_button = ttk.Button(team_frame, text="Next", command=show_player_frame)
next_to_player_button.grid(row=2, column=2, padx=5, pady=5, sticky='ew')

# New buttons for sorting
sort_by_weight_button = ttk.Button(team_frame, text="Sort by Weight", command=lambda: sort_roster('WEIGHT'))
sort_by_weight_button.grid(row=2, column=0, padx=5, pady=5, sticky='ew')

sort_by_height_button = ttk.Button(team_frame, text="Sort by Height", command=lambda: sort_roster('HEIGHT'))
sort_by_height_button.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

# In the team_frame
next_to_player_button = ttk.Button(team_frame, text="Next", command=show_player_frame)
next_to_player_button.grid(row=2, column=2, padx=5, pady=5, sticky='ew')

back_button = ttk.Button(team_frame, text="Back", command=back_to_teams_frame)
back_button.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

# Player section (below both team sections)
player_frame = ttk.Frame(root, padding="10", style='TFrame')
player_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

player_label = ttk.Label(player_frame, text="Player ID:")
player_label.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

player_id_entry = ttk.Entry(player_frame, width=15)
player_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

show_stats_button = ttk.Button(player_frame, text="Show Player Stats", command=show_player_stats)
show_stats_button.grid(row=0, column=2, padx=5, pady=5, sticky='ew')

player_stats_text_box = scrolledtext.ScrolledText(player_frame, width=80, height=10, state=tk.DISABLED)
player_stats_text_box.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

save_stats_button = ttk.Button(player_frame, text="Save Player Stats", command=save_player_stats)
save_stats_button.grid(row=2, column=0, padx=5, pady=5, sticky='ew')

predict_stats_button = ttk.Button(player_frame, text="Predict Player Stats", command=lambda: predict_player_stats(player_id_entry.get()))
predict_stats_button.grid(row=2, column=2, padx=5, pady=5, sticky='ew')

# In the player_frame
next_to_predicted_stats_button = ttk.Button(player_frame, text="Next", command=show_predicted_stats_frame)
next_to_predicted_stats_button.grid(row=3, column=2, padx=5, pady=5, sticky='ew')

back_button = ttk.Button(player_frame, text="Back", command=back_to_team_frame)
back_button.grid(row=3, column=0, padx=5, pady=5, sticky='ew')

# New frame for predicted stats and related buttons
predicted_stats_frame = ttk.Frame(root, padding="10", style='TFrame')

# Label for predicted stats
predicted_stats_label = ttk.Label(predicted_stats_frame, text="Predicted Player Stats (2024-2025 Season):")
predicted_stats_label.grid(row=0, column=0, columnspan=7, padx=5, pady=5, sticky='w')


# Create labels for the column headers
column_headers = ['PTS', 'REB', 'AST', 'BLK', 'STL', 'FG%', '3PT%']
predicted_stats_entries = {}
for col, header in enumerate(column_headers):
    ttk.Label(predicted_stats_frame, text=header, style='Header.TLabel').grid(row=1, column=col, padx=5, pady=5, sticky='ew')
    entry = ttk.Entry(predicted_stats_frame, width=10, state='readonly')
    entry.grid(row=2, column=col, padx=5, pady=5, sticky='ew')
    entry.configure(background='white', foreground='black')
    predicted_stats_entries[header] = entry

# Button to save predicted stats
save_predicted_stats_button = ttk.Button(predicted_stats_frame, text="Save Predicted Stats", command=lambda: save_stats_to_excel(pd.DataFrame([predicted_stats_entries]), "predicted_stats.xlsx"))
save_predicted_stats_button.grid(row=3, column=2, padx=5, pady=5, sticky='ew')

# Button to go back
back_button = ttk.Button(predicted_stats_frame, text="Back", command=back_to_players_frame)
back_button.grid(row=3, column=0, padx=5, pady=5, sticky='ew')

# In the predicted_stats_frame
back_button = ttk.Button(predicted_stats_frame, text="Back to Teams", command=back_to_teams_frame)
back_button.grid(row=3, column=4, padx=5, pady=5, sticky='ew')

# Create a frame for the start screen using tk.Frame
start_screen_frame = tk.Frame(root, bg='lightblue', padx=10, pady=10)
start_screen_frame.place(relx=0.5, rely=0.5, anchor='center')

# Create a label for the start screen with custom font size
start_screen_label = tk.Label(start_screen_frame, text="Welcome to the NBA Stats Application", bg='lightblue', fg='darkblue', font=('Helvetica', 18, 'bold'))
start_screen_label.pack(pady=10)


# Configure row and column weights to make the frame centered
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

view_teams_button = ttk.Button(start_screen_frame, text="View Teams", command=show_teams_frame)
view_teams_button.pack(pady=5)

exit_button = ttk.Button(start_screen_frame, text="Exit", command=exit_program)
exit_button.pack(pady=20)

# Start with the start screen frame
show_start_screen()

root.mainloop()
