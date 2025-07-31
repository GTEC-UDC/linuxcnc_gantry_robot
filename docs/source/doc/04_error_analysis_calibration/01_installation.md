# Installation and Basic Usage

1. **Install dependencies**: Use `uv` or `pip` to create a virtual environment and install the required Python packages.

   - With `uv`:

     ```bash
     uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
     ```

   - With `pip`:

     ```bash
     python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
     ```

2. **Prepare the data**: The system requires both gantry position data (CSV) and OptiTrack motion capture data (CSV) in the expected formats (see {ref}`sec:data_format` section).

3. **Add a configuration file**: Create a `config.json` file with the calibration settings.

4. **Run the calibration script**: Execute the calibration script `run_calibration.py` to generate a `calibration.json` file with the alignment and correction parameters.

5. **Visualize the results**: Use the plotting scripts to visualize the results.

See {ref}`sec:usage` section for more details on how to use the scripts.