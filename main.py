
"""play:                   python main.py
Headless AI vs AI test: python main.py --headless --matches 100 --difficulty Medium
"""

import argparse
import os
import sys

from maze_hunter.analysis.stats import BatchResults, benchmark_search
from maze_hunter.config.settings import DIFFICULTY_NAMES,DT,MODE_AI_VS_AI
from maze_hunter.core.game import Game
from maze_hunter.core.maze import Maze

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_headless(matches, difficulty, out_csv):
    {
        maze = Maze()
        batch = BatchResults(matches)

        for i in range(matches):
            game = Game(MODE_AI_VS_AI,difficulty,seed=i,maze=maze)
            while not game.result:
                game.update(DT)
            batch.add(game)
            row = batch.rows[-1]
            print(f"match {i + 1:3d}/{matches}: {row['result']:<10} score {row['score']:5d} "
              f"level {row['level']}  {row['time_s']:5.1f}s")
    print(f"\n=== AI vs AI results ({difficulty}) ===")
    for line in batch.summary_lines():
        print(line)
    bench = benchmark_search(maze,pairs=1000)
    print("\n=== A* vs BFS on the same 1000 random start/goal pairs ===")
    for name, b in bench.items():
        print(f"{name:<4} avg nodes expanded {b['avg_nodes']:6.1f}   avg time {b['avg_ms']:.4f} ms   "
              f"avg path length {b['avg_path']:.1f}")
    batch.save_csv(out_csv)
    print(f"\nPer-match results saved to {out_csv}")

    def main(argv=None):
    parser = argparse.ArgumentParser(description="Maze Hunter - an AI maze chase game")
    parser.add_argument("--headless", action="store_true", help="run AI vs AI matches without a window")
    parser.add_argument("--matches", type=int, default=100, help="number of headless matches")
    parser.add_argument("--difficulty", choices=DIFFICULTY_NAMES, default="Medium")
    parser.add_argument("--out", default=os.path.join(ROOT, "results.csv"), help="CSV file for results")
    args = parser.parse_args(argv)
    if args.headless:
        run_headless(args.matches, args.difficulty, args.out)
    else:
        from maze_hunter.ui.app import App     # pygame is only needed for the window
        App().run()


if __name__ == "__main__":
    sys.exit(main())


            
                
            
            
        

    }


