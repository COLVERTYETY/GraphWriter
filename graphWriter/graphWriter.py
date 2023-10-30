
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.progress import Progress
from collections import defaultdict
from torch.utils.tensorboard import SummaryWriter
import asciichartpy as acp
from rich.layout import Layout
from rich.text import Text

class PlotHandler:
    """
    Handles the rendering of a single plot in a Rich Console.

    The PlotHandler class encapsulates the data and rendering logic for a single
    plot, ensuring it is displayed with the correct dimensions within a Rich Console.

    Attributes:
        tag (str): The tag associated with the plot, used for the title.
        data (list): The data points to be plotted.

    Methods:
        __rich_console__(console: Console, options: ConsoleOptions) -> RenderResult:
            Renders the plot within a panel, using the available space provided by
            the Rich Console.
    """
    def __init__(self, tag:str, data:list) -> None:
        self.tag = tag
        self.data = data

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width, height = options.max_width, options.height
        title = f"~~ [bold][yellow]{self.tag}[/bold][/yellow] ~~"
        panel = Panel(acp.plot(self.data[-width+14:], {'height': height-4}), expand=True, title=title)
        yield panel

class GraphWriter:
    def __init__(self, writer:SummaryWriter, max_print_lines=5, max_progress_lines=3):
        """
        A class used to write and display scalars to tensorboard, and visualize the training and testing process 
        in the terminal using rich library.

        ...

        Attributes
        ----------
        writer : SummaryWriter
            a torch SummaryWriter object to log scalars for tensorboard
        max_progress_lines : int
            the maximum number of lines to be used for displaying progress bars
        max_print_lines : int
            the maximum number of lines to be used for displaying print statements
        scalar_data : dict
            a dictionary to hold scalar values
        scalar_layouts : dict
            a dictionary to hold layouts for each scalar
        scalar_groups : defaultdict(Layout)
            a dictionary to hold layouts grouped by prefix
        scalar_panels : Layout
            a layout for holding all scalar panels
        console : Console
            a rich Console object for rendering text and layouts to the terminal
        progress : Progress
            a rich Progress object for displaying progress bars
        progress_bars : dict
            a dictionary to hold progress bars by description
        layout : Layout
            a layout to hold all other layouts
        print_panel_content : Text
            a Text object to hold print statements
        print_text : str
            a string to accumulate printed text

        Methods
        -------
        add_scalar(tag, scalar_value, global_step=None)
            Logs a scalar value to tensorboard and updates the scalar panel
        parse_tag(tag)
            Parses a tag into a prefix and name
        update_scalars(tag)
            Updates the scalar panels with new data
        update_progress()
            Updates the progress layout
        update_print(**kwargs)
            Updates the print layout
        get_panel(tag, data, width, height)
            Returns a panel with a plot of scalar values
        print(*args, **kwargs)
            Custom print function to display text in the print layout
        track(iterable, description="Processing...")
            Yields items from an iterable and updates a progress bar
        """
        self.writer = writer
        self.max_progress_lines = max_progress_lines
        self.max_print_lines = max_print_lines 
        self.scalar_data = {}
        self.scalar_layouts = {}
        self.scalar_groups = defaultdict(Layout)
        self.scalar_panels = Layout()
        self.console = Console()
        self.progress = Progress()
        self.progress_bars = {}
        self.layout = Layout()
        self.layout.split(
            Layout(name='spacer', size=1),
            Layout(self.scalar_panels,name='scalars', ratio=6),
            Layout(name='progress', size=max_progress_lines, ratio=2),
            Layout(name='prints', size=max_print_lines+2, ratio=2)
        )
        self.print_panel_content = Text()
        self.print_text = ""

    def add_scalar(self, tag, scalar_value, global_step=None, display=True) -> None:
        """Logs a scalar value to tensorboard and updates the scalar panel."""
        self.writer.add_scalar(tag, scalar_value, global_step)
        if tag not in self.scalar_data:
            self.scalar_data[tag] = []
        self.scalar_data[tag].append(scalar_value)
        if display:
            self.update_scalars(tag)

    def group_scalars_by_prefix(self)-> defaultdict:
        grouped_scalars = defaultdict(dict)
        for tag, data in self.scalar_data.items():
            prefix, _ = self.parse_tag(tag)
            grouped_scalars[prefix][tag] = data
        return grouped_scalars

    def parse_tag(self, tag:str) -> tuple:
        """Parses a tag into a prefix and name."""
        if '/' in tag:
            prefix, name = tag.split('/', 1)
        else:
            prefix, name = None, tag
        return prefix, name

    def update_scalars(self, tag:str) -> None:
        """Updates the scalar panels with new data."""
        prefix, name = self.parse_tag(tag)
        data = self.scalar_data[tag]

        plot_handler = PlotHandler(tag, data)

        if tag not in self.scalar_layouts:
            # Create a new layout for the scalar
            new_scalar_layout = Layout(plot_handler, name=tag)
            self.scalar_layouts[tag] = new_scalar_layout
            if prefix in self.scalar_groups:
                existing_group_layout = self.scalar_groups[prefix]
                existing_group_layout.split_row(
                    *existing_group_layout.children,
                    new_scalar_layout,
                )
            else:
                new_group_layout = Layout()
                new_group_layout.split_row(new_scalar_layout)
                self.scalar_groups[prefix] = new_group_layout
            self.scalar_panels.split_column(*self.scalar_groups.values())
        else:
            existing_scalar_layout = self.scalar_layouts[tag]
            existing_scalar_layout.update(plot_handler)

        self.console.print(self.layout, overflow='crop')

    def update_progress(self) -> None:
        """Updates the progress layout."""
        progress_layout = self.layout['progress']
        progress_layout.update(self.progress)
        self.console.print(self.layout)
    
    def print(self, *args, **kwargs) -> None:
        """Custom print function to display text in the print layout."""
        message = ' '.join(str(arg) for arg in args)
        self.print_text += f"{message}\n"
        lines = self.print_text.split('\n')
        if len(lines) > self.max_print_lines:
            trimmed_text = '\n'.join(lines[-self.max_print_lines:])
            self.print_text = trimmed_text
        else:
            trimmed_text = self.print_text
        print_layout = self.layout['prints']
        print_layout.update(Panel(trimmed_text))
        self.console.print(self.layout, **kwargs)

    def track(self, iterable, description="Processing...") -> None:
        """Yields items from an iterable and updates a progress bar."""
        if description in self.progress_bars:
            task_id = self.progress_bars[description]
            self.progress.reset(task_id)
        else:
            task_id = self.progress.add_task(description, total=len(iterable))
            self.progress_bars[description] = task_id
        
        for item in iterable:
            yield item
            self.progress.update(task_id, advance=1)
            self.update_progress()

if __name__ == "__main__":
    import time
    import math
    import random

    # Usage
    writer = SummaryWriter()
    graph_writer = GraphWriter(writer)
    graph_writer.print("simulating training...")

    resume = iter([
    "Unveil the [bold underline]magic[/bold underline] of your machine learning models in real-time with our [bold yellow]GraphWriter[/bold yellow] !",
    "Leveraging the elegance of the [bold blue underline]Rich[/bold blue underline] library and the backbone of [red ]Torch's SummaryWriter[/red], it morphs your terminal into a [bold yellow reverse]vibrant dashboard[/bold yellow reverse].",
    "Meet [bold magenta reverse]GraphWriter[/bold magenta reverse], your new sidekick, turning logs into [bold cyan]lively plots[/bold cyan] and [bold green]progress bars[/bold green] right in your console!",
    "Say adieu to mundane print statements, and hello to a rolling log of [green italic]insights[/green italic].",
    "Now, every epoch and batch march on-screen with [bold yellow]visual fanfare[/bold yellow].",
    "It's not just coding; it's hosting a live, interactive show of your model's [bold cyan underline]triumphs[/bold cyan underline]!",
    "So, what are you waiting for? [bold red]Get started[/bold red] with [bold yellow]GraphWriter[/bold yellow] today!",])

    for e in graph_writer.track(range(100), description="epochs"):
        for t in graph_writer.track(range(100), description="training"):
            # time.sleep(0.01)
            # Simulate a training loss that generally decreases over time with some noise
            train_loss = 3*math.exp(-0.1*e + 0.1*random.gauss(0, 1)) 
            train_acc =  100 - 20 * math.exp(-1.5*e/30) - random.randrange(0, 90)/(e+1)
        graph_writer.add_scalar('Train/Loss', train_loss, global_step=t + e*100)
        graph_writer.add_scalar('Train/Acc', train_acc, global_step=t + e*100)

        for t in graph_writer.track(range(100), description="testing"):
            # time.sleep(0.01)
            # Simulate a testing loss that generally decreases over time with some noise
            test_loss = 2*math.exp(-0.1*e+ 0.2*random.gauss(0, 1)) 
            # test_acc = 0.5 + 0.5*math.tanh(0.1*(e - 50)) + 0.05*random.randrange(0, 80)
            test_acc =  100 - 20 * math.exp(-2.0*e/30) - random.randrange(0, 90)/(e+1)
        graph_writer.add_scalar('Test/Loss', test_loss, global_step=t + e*100)
        graph_writer.add_scalar('Test/Acc', test_acc, global_step=t + e*100)

        graph_writer.add_scalar('Epochs', e, global_step=e)
        if e % 2 == 0:
            graph_writer.print(next(resume, f"[bold]Processing[/bold] epoch [blue]{e}[/blue] Accuracy: [green]{test_acc:.2f}[/green]"))
     
