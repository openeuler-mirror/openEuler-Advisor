#!/usr/bin/env python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2024. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************
"""
Interactive PR reviewer for openEuler-Advisor.
This script allows users to browse and select PRs to review using keyboard navigation.
"""

import sys
import os
import argparse
import subprocess
from typing import List, Dict, Any, Optional
import curses
from curses import wrapper

from advisors.get_openeuler_pending_pr import get_quickissue_pulls_by_repo, get_quickissue_pulls_by_sig


class PRSelector:
    def __init__(self, prs: List[Dict[str, Any]], reviewed_prs: set = None):
        self.prs = prs
        self.current_index = 0
        self.selected_pr = None
        self.window = None
        self.max_lines = 0
        self.max_cols = 0
        self.scroll_offset = 0
        self.reviewed_prs = reviewed_prs or set()

    def refresh_display(self):
        """Refresh the PR selection display"""
        self.window.clear()
        self.window.border()

        # Title
        title = "Select PR to Review"
        self.window.addstr(1, (self.max_cols - len(title)) // 2, title, curses.A_BOLD)

        # Instructions
        instructions = [
            "↑/↓: Navigate | Enter: Review | q: Quit | i: PR Info | r: Refresh"
        ]
        for i, instruction in enumerate(instructions):
            self.window.addstr(3, 2, instruction)

        # Calculate display range
        start_line = min(self.scroll_offset, len(self.prs) - 1)
        end_line = min(start_line + self.max_lines - 8, len(self.prs))

        # Display PRs
        for idx in range(start_line, min(end_line, len(self.prs))):
            pr = self.prs[idx]
            line_num = idx - start_line + 5

            # Check if this PR was reviewed
            pr_key = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
            is_reviewed = pr_key in self.reviewed_prs

            # Prepare PR line
            pr_line = f"{idx + 1:3d}. {pr['owner']}/{pr['repo']}#{pr['number']}"
            if is_reviewed:
                pr_line += " ✓"  # Mark as reviewed
            if pr.get('title'):
                pr_line += f" - {pr['title'][:60]}"
                if len(pr['title']) > 60:
                    pr_line += "..."
            if pr.get('author'):
                pr_line += f" by {pr['author']}"

            # Apply highlighting
            if idx == self.current_index:
                pr_line = pr_line[:self.max_cols - 6]
                attr = curses.A_REVERSE
                if is_reviewed:
                    attr |= curses.A_DIM  # Dim reviewed items
                self.window.addstr(line_num, 2, pr_line, attr)
            else:
                pr_line = pr_line[:self.max_cols - 4]
                attr = curses.A_DIM if is_reviewed else curses.A_NORMAL
                self.window.addstr(line_num, 2, pr_line, attr)

        # Status bar
        reviewed_count = len(self.reviewed_prs)
        status = f"PR {self.current_index + 1}/{len(self.prs)} | Reviewed: {reviewed_count}/{len(self.prs)} | "
        if self.prs:
            pr = self.prs[self.current_index]
            status += f"Owner: {pr['owner']}/{pr['repo']} | "
            status += f"Author: {pr.get('author', 'N/A')} | "
            status += f"State: {pr.get('state', 'N/A')}"
        self.window.addstr(self.max_lines - 2, 2, status)

        self.window.refresh()

    def move_up(self):
        """Move selection up"""
        if self.current_index > 0:
            self.current_index -= 1
            if self.current_index < self.scroll_offset:
                self.scroll_offset = self.current_index

    def move_down(self):
        """Move selection down"""
        if self.current_index < len(self.prs) - 1:
            self.current_index += 1
            if self.current_index >= self.scroll_offset + self.max_lines - 8:
                self.scroll_offset = self.current_index - self.max_lines + 9

    def show_pr_info(self):
        """Show detailed information about the selected PR"""
        if not self.prs:
            return

        pr = self.prs[self.current_index]

        # Create a new window for PR info
        info_height = min(25, self.max_lines - 5)
        info_width = min(100, self.max_cols - 10)
        info_win = curses.newwin(info_height, info_width,
                                (self.max_lines - info_height) // 2,
                                (self.max_cols - info_width) // 2)
        info_win.border()

        # Title
        title = "PR Details"
        info_win.addstr(1, (info_width - len(title)) // 2, title, curses.A_BOLD)
        info_win.addstr(2, 1, "=" * (info_width - 2))

        # PR information
        info_lines = [
            f"Repository: {pr['owner']}/{pr['repo']}",
            f"PR Number: #{pr.get('number', 'N/A')}",
            f"Title: {pr.get('title', 'N/A')}",
            f"Author: {pr.get('author', 'N/A')}",
            f"State: {pr.get('state', 'N/A')}",
            f"Created: {pr.get('created_at', 'N/A')}",
            f"Updated: {pr.get('updated_at', 'N/A')}",
            f"URL: {pr.get('url', 'N/A')}",
        ]

        if pr.get('labels'):
            labels = pr['labels'] if isinstance(pr['labels'], list) else pr['labels'].split(', ')
            info_lines.append(f"Labels: {', '.join(labels)}")

        if pr.get('assignees'):
            assignees = pr['assignees'] if isinstance(pr['assignees'], list) else pr['assignees'].split(',')
            info_lines.append(f"Assignees: {', '.join(assignees)}")

        if pr.get('description'):
            desc = pr['description'][:200] + "..." if len(pr['description']) > 200 else pr['description']
            info_lines.append(f"Description: {desc}")

        # Display info
        for i, line in enumerate(info_lines[:info_height - 4]):
            if len(line) > info_width - 4:
                # Wrap long lines
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) <= info_width - 4:
                        current_line += word + " "
                    else:
                        info_win.addstr(4 + i, 2, current_line)
                        i += 1
                        if i >= info_height - 4:
                            break
                        current_line = word + " "
                else:
                    if current_line and i < info_height - 4:
                        info_win.addstr(4 + i, 2, current_line)
            else:
                info_win.addstr(4 + i, 2, line)

        info_win.addstr(info_height - 2, (info_width - 20) // 2, "Press any key to close")
        info_win.refresh()

        # Wait for key press
        info_win.getch()
        info_win.clear()
        info_win.refresh()

    def run_selection(self, stdscr):
        """Main selection loop"""
        self.window = stdscr
        self.max_lines, self.max_cols = stdscr.getmaxyx()

        # Hide cursor
        curses.curs_set(0)

        # Enable keypad
        stdscr.keypad(True)

        # Initial refresh
        self.refresh_display()

        while True:
            key = stdscr.getch()

            if key == curses.KEY_UP or key == ord('k'):
                self.move_up()
                self.refresh_display()
            elif key == curses.KEY_DOWN or key == ord('j'):
                self.move_down()
                self.refresh_display()
            elif key == ord('q') or key == ord('Q'):
                return None
            elif key == ord('\n') or key == ord('\r'):
                if self.prs:
                    self.selected_pr = self.prs[self.current_index]
                    return self.selected_pr
            elif key == ord('i') or key == ord('I'):
                self.show_pr_info()
                self.refresh_display()


def review_pr_with_oe_review(pr: Dict[str, Any], ai_model: str = None):
    """Review the selected PR using review_pr standalone module"""
    print(f"\nReviewing PR: {pr['owner']}/{pr['repo']}#{pr['number']}")
    print(f"Title: {pr.get('title', 'N/A')}")
    print(f"Author: {pr.get('author', 'N/A')}")
    print("-" * 60)

    # Build review_pr command
    cmd = ["oe_review"]
    cmd.extend(["-n", pr['owner']+"/"+pr['repo']])
    cmd.extend(["-p", str(pr['number'])])

    if ai_model:
        cmd.extend(["-i", ai_model])

    # Run review_pr
    try:
        print(cmd)
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\nReview interrupted by user")
    except Exception as e:
        print(f"Error running review_pr: {e}")


def continuous_review_loop(prs: List[Dict[str, Any]], ai_model: str = None):
    """Run continuous review loop, returning to selection after each review"""
    reviewed_prs = set()  # Track reviewed PRs

    while True:
        # Run interactive selection
        selected_pr = wrapper(PRSelector(prs, reviewed_prs).run_selection)

        if not selected_pr:
            # User quit
            print("\nNo PR selected. Exiting.")
            break

        # Check if PR was already reviewed
        pr_key = f"{selected_pr['owner']}/{selected_pr['repo']}#{selected_pr['number']}"
        if pr_key in reviewed_prs:
            # Ask if user wants to review again
            print(f"\nWARNING: PR {pr_key} was already reviewed!")
            choice = input("Review again? (y/N): ").strip().lower()
            if choice != 'y':
                continue

        # Temporarily exit curses mode for review
        # curses.endwin()

        # Review the selected PR
        print(f"\n{'='*60}")
        print(f"Starting review for: {pr_key}")
        print(f"{'='*60}")

        # Run the review
        review_pr_with_oe_review(selected_pr, ai_model)

        # Mark as reviewed
        reviewed_prs.add(pr_key)

        # Show completion status
        print(f"\n{'='*60}")
        print(f"Review completed for: {pr_key}")
        print(f"Total PRs reviewed: {len(reviewed_prs)}/{len(prs)}")
        print(f"{'='*60}")

        # Ask if user wants to continue
        if len(reviewed_prs) >= len(prs):
            print("\nAll PRs have been reviewed!")
            choice = input("Press Enter to exit...").strip()
            break

def main():
    parser = argparse.ArgumentParser(
        description="Interactive PR selector and reviewer for openEuler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sig infra
  %(prog)s --repo src-openeuler python-marshmallow
  %(prog)s --sig devkit --model gpt-4
        """
    )

    # Query options
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("-s", "--sig", help="SIG name")
    query_group.add_argument("-r", "--repo", nargs=2, metavar=('OWNER', 'REPO'),
                           help="Repository owner and name")

    # Review options
    parser.add_argument("--model", help="AI model to use for review")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    # Fetch PRs
    print("Fetching PRs...", flush=True)
    if args.sig:
        prs, total = get_quickissue_pulls_by_sig(args.sig, args.verbose)
    else:  # repo
        owner, repo = args.repo
        prs, total = get_quickissue_pulls_by_repo(owner, repo, args.verbose)

    if not prs:
        print("No PRs found.")
        return

    print(f"\nFound {len(prs)} available PRs")
    # Run continuous review loop
    continuous_review_loop(prs, args.model)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
