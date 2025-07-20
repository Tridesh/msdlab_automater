#!/usr/bin/env python3

"""
ENHANCED TCAD TCL Command Generator – Multi-Mode Version (Modified)

- Mode 1: Multiple nodes, user TDRs, optional last TDR with just node prefix
- Mode 2: Multiple nodes with PLT files
- Mode 3: Multiple cutplane/cutline/parameter sets

Modifications:
1. Multiple parameters support (comma-separated) for Mode 1 and Mode 3
2. Simplified TDR code entry (last 2 digits only)
3. File naming: currentvalue_parameter_tdrcode
4. Fixed 2D plot generation for all parameter sets in Mode 1
"""

def get_axis_mapping(cutplane_axis: str, cutline_axis: str) -> str:
    all_axes = {"X", "Y", "Z"}
    removed_axes = {cutplane_axis.upper(), cutline_axis.upper()}
    return list(all_axes - removed_axes)[0]

def get_export_variables(cutplane_axis: str, cutline_axis: str, parameter: str):
    axis_x = get_axis_mapping(cutplane_axis, cutline_axis)
    return [axis_x, parameter]

def format_tdr_code(user_input: str) -> str:
    """Convert 2-digit user input to 4-digit TDR code (e.g., '01' -> '0001')"""
    return f"00{user_input.zfill(2)}"

def parse_parameters(param_string: str) -> list:
    """Parse comma-separated parameters and clean them"""
    return [param.strip() for param in param_string.split(',') if param.strip()]

# ──────────────────────────────────────────────
# Mode 1: Many nodes with user TDRs and optional last TDR (MODIFIED)
# ──────────────────────────────────────────────

def generate_mode1_commands():
    print("=" * 80)
    print("MODE 1: Many nodes with user TDRs (with optional last TDR, flexible prefix)")
    print("=" * 80)
    
    try:
        num_nodes = int(input("Enter the number of nodes to analyze: "))
        node_names = []
        for i in range(num_nodes):
            node = input(f"Enter node name for node {i+1} (e.g., n1257_I4.6): ")
            node_names.append(node)
        
        no_of_tdrs = int(input("Enter the number of TDRs: "))
        tdr_codes = []
        for i in range(no_of_tdrs):
            code = input(f"Enter last 2 digits of TDR-{i+1} code (e.g., 02 for 0002): ")
            tdr_codes.append(format_tdr_code(code))
        
        need_last_tdr = input(
            "Do you need to include a last TDR with just the node prefix (e.g., n1257)? (yes/no): "
        ).lower()
        
        base_path = input("Enter base file path: ")
        if not base_path.endswith('/'):
            base_path += '/'
        
        # Get current value for file naming
        current_value = input("Enter current value for file naming: ")
        
        parameters = [
            "ConductionBandEnergy", "ConductionCurrentDensity", "DopingConcentration",
            "EffectiveIntrinsicDensity", "ElectricField", "ElectrostaticPotential",
            "EquilibriumPotential", "Impactionization", "IntrinsicDensity",
            "LatticeTemperature", "QuasiFermiPotential", "SpaceCharge",
            "ValenceBandEnergy", "eAlphaAvalanche", "eCurrentDensity", "eDensity",
            "eMobility", "eQuasiFermiPotential", "hAlphaAvalanche", "hCurrentDensity",
            "hDensity", "hMobility", "hQuasiFermiPotential"
        ]
        
        print("\nAvailable parameters:")
        for p in parameters:
            print(f" • {p}")
        
        cutplane_cutline_sets = []
        while True:
            cutplane_axis = input("Enter cutplane axis (x/y/z): ").lower()
            while cutplane_axis not in {'x', 'y', 'z'}:
                cutplane_axis = input("Invalid axis. Enter cutplane axis (x/y/z): ").lower()
            
            cutplane_position = input(f"Enter cutplane position on {cutplane_axis}-axis: ")
            
            cutline_axis = input("Enter cutline axis (x/y/z): ").lower()
            while cutline_axis not in {'x', 'y', 'z'}:
                cutline_axis = input("Invalid axis. Enter cutline axis (x/y/z): ").lower()
            
            if cutline_axis == cutplane_axis:
                print("Error: Cutplane and cutline cannot be on the same axis!")
                return []
            
            print(f"\nCutline positions for each TDR on {cutline_axis}-axis:")
            cutline_positions = []
            for code in tdr_codes:
                pos = input(f" Position for TDR {code}: ")
                cutline_positions.append(pos)
            
            # Modified to accept multiple parameters
            param_input = input("Enter parameter(s) for this set (comma-separated if multiple): ")
            param_list = parse_parameters(param_input)
            
            # Validate all parameters
            invalid_params = [p for p in param_list if p not in parameters]
            if invalid_params:
                print(f"Invalid parameter(s): {', '.join(invalid_params)}. Please choose from the available list.")
                continue
            
            cutplane_cutline_sets.append({
                'cutplane_axis': cutplane_axis,
                'cutplane_position': cutplane_position,
                'cutline_axis': cutline_axis,
                'cutline_positions': cutline_positions,
                'parameters': param_list  # Changed from 'parameter' to 'parameters'
            })
            
            more = input("Do you want to enter another set of cutplane and cutline? (yes/no): ").lower()
            if more not in ['yes', 'y']:
                break
        
        y_axis_type = input("Enter Y-axis type (linear/log) [default: log]: ").lower() or 'log'
        if y_axis_type not in {'linear', 'log'}:
            y_axis_type = 'log'
        
        csv_export_path = input("Enter CSV export path: ")
        if not csv_export_path.endswith('/'):
            csv_export_path += '/'
        
        csv_filename = input("Enter CSV filename (without extension): ")
        
        cmds = []
        cmds += [
            "################################################",
            "# Sentaurus Visual Console - Tcl version 8.6.6 #",
            "################################################",
            "# "
        ]
        
        # Process each cutplane-cutline set and its parameters
        unified_1d_plots = []
        curve_counter = 1
        
        for set_idx, cutset in enumerate(cutplane_cutline_sets, start=1):
            cp_axis = cutset['cutplane_axis']
            cp_pos = cutset['cutplane_position']
            cl_axis = cutset['cutline_axis']
            cl_positions = cutset['cutline_positions']
            parameters_list = cutset['parameters']
            
            axis_x = get_axis_mapping(cp_axis, cl_axis)
            
            for param_idx, parameter in enumerate(parameters_list):
                # Load files with parameter-specific naming: currentvalue_parameter_tdrcode
                file_bases_for_param = []
                for node in node_names:
                    for code in tdr_codes:
                        file_base = f"{current_value}_{parameter}_{code}"
                        file_bases_for_param.append(file_base)
                        fname = f"{file_base}_des.tdr"
                        dset = f"{file_base}_des"
                        plot = f"Plot_{dset}"
                        
                        cmds += [
                            f"load_file {base_path}{fname} -fod",
                            f"create_plot -dataset {dset}",
                            f"select_plots {{{plot}}}",
                            f"# {plot}", "", f"# {plot}", "", f"# {dset}"
                        ]
                
                # Handle last TDR if needed
                if need_last_tdr in ['yes', 'y']:
                    last_prefix = node_names[0].split('_')[0]
                    file_base = f"{current_value}_{parameter}_{last_prefix}"
                    file_bases_for_param.append(file_base)
                    fname = f"{file_base}_des.tdr"
                    dset = f"{file_base}_des"
                    plot = f"Plot_{dset}"
                    
                    cmds += [
                        f"load_file {base_path}{fname} -fod",
                        f"create_plot -dataset {dset}",
                        f"select_plots {{{plot}}}",
                        f"# {plot}", "", f"# {plot}", "", f"# {dset}"
                    ]
                
                # Link plots for this parameter
                first_plot = f"Plot_{file_bases_for_param[0]}_des"
                all_plots_for_param = [f"Plot_{fb}_des" for fb in file_bases_for_param]
                all_plots_str = " ".join(all_plots_for_param)
                
                cmds += [
                    f"select_plots {{{first_plot}}}",
                    f"# {first_plot}",
                    f"select_plots {{{all_plots_str}}}",
                    f"# {all_plots_str}",
                    f"link_plots {{{all_plots_str}}}",
                    "# 1"
                ]
                
                # Set field property for the last plot
                last_plot = all_plots_for_param[-1]
                last_dset = last_plot.replace("Plot_", "")
                
                cmds += [
                    f"set_field_prop {parameter} -plot {last_plot} -geom {last_dset} -show_bands",
                    "# 0"
                ]
                
                # Create cutplanes for all files of this parameter
                for file_base in file_bases_for_param:
                    plot = f"Plot_{file_base}_des"
                    cmds += [
                        f"select_plots {{{plot}}}",
                        f"# {plot}",
                        f"create_cutplane -plot {plot} -type {cp_axis} -at {cp_pos}",
                        f"# C{set_idx}({file_base}_des)"
                    ]
                
                # Create plots for cutplanes
                for file_base in file_bases_for_param:
                    cp_dset = f"C{set_idx}({file_base}_des)"
                    plot = f"Plot_{file_base}_des"
                    cmds += [
                        f"create_plot -dataset {cp_dset} -ref_plot {plot}",
                        f"select_plots {{Plot_{cp_dset}}}",
                        f"# Plot_{cp_dset}", "", f"# Plot_{cp_dset}"
                    ]
                
                # Create cutlines
                for i, file_base in enumerate(file_bases_for_param):
                    cp_plot = f"Plot_C{set_idx}({file_base}_des)"
                    cl_pos = cl_positions[i % len(cl_positions)]
                    cmds += [
                        f"select_plots {{{cp_plot}}}",
                        f"# {cp_plot}",
                        f"create_cutline -plot {cp_plot} -type {cl_axis} -at {cl_pos}",
                        f"# C1(C{set_idx}({file_base}_des))"
                    ]
                
                # Create unified 1D plot for this parameter
                unified_1d_plot = f"Plot_C1(C{set_idx}({file_bases_for_param[0]}_des))_S{set_idx}P{param_idx}"
                first_cl_dset = f"C1(C{set_idx}({file_bases_for_param[0]}_des))"
                unified_1d_plots.append(unified_1d_plot)
                
                cmds += [
                    f"create_plot -dataset {first_cl_dset} -1d",
                    f"select_plots {{{unified_1d_plot}}}",
                    f"# {unified_1d_plot}", "", f"# {unified_1d_plot}"
                ]
                
                # Create curves for this parameter
                curves_for_this_plot = []
                for i, file_base in enumerate(file_bases_for_param):
                    cl_dset = f"C1(C{set_idx}({file_base}_des))"
                    cmds += [
                        f"create_curve -axisX {axis_x} -axisY {parameter} -dataset {{{cl_dset}}} -plot {unified_1d_plot}",
                        f"# Curve_{curve_counter}",
                        f"set_axis_prop -plot {unified_1d_plot} -axis y -type {y_axis_type}",
                        f"set_axis_prop -plot {unified_1d_plot} -axis x -range {{-0.9 9.0}}",
                        "# 0"
                    ]
                    curves_for_this_plot.append(f"Curve_{curve_counter}")
                    curve_counter += 1
                
                # Export curves to CSV for this parameter
                curve_names = " ".join(curves_for_this_plot)
                csv_full_path = f"{csv_export_path}{csv_filename}_set{set_idx}_param_{parameter}.csv"
                
                cmds += [
                    f"select_plots {{{unified_1d_plot}}}",
                    f"# {unified_1d_plot}",
                    f"export_curves {{{curve_names}}} -plot {unified_1d_plot} -filename {csv_full_path} -format csv",
                    f"# {csv_full_path}"
                ]
        
        return cmds
        
    except (ValueError, KeyboardInterrupt):
        print("Input error or operation cancelled.")
        return []

# ──────────────────────────────────────────────
# Mode 2: Different nodes with PLT files (NO CHANGES NEEDED)
# ──────────────────────────────────────────────

def generate_mode2_commands():
    print("=" * 80)
    print("MODE 2: Different nodes with PLT files (Enhanced with Styling)")
    print("=" * 80)
    
    try:
        # Get user inputs
        print("File Path Configuration:")
        base_path = input("Enter base file path: ")
        if not base_path.endswith('/'):
            base_path += '/'
        
        print("\nPLT File Configuration:")
        plt_prefix = input("Enter PLT file prefix (e.g., DeMOS): ")
        
        print("\nNode Configuration:")
        num_nodes = int(input("Enter the number of nodes: "))
        nodes_data = []
        for i in range(num_nodes):
            print(f"\nNode {i+1} Configuration:")
            version = input(f"Enter version for node {i+1} (e.g., 4.5): ")
            node_id = input(f"Enter node ID for node {i+1} (e.g., n1250): ")
            nodes_data.append((version, node_id))
        
        # CSV export configuration
        print("\nCSV Export Configuration:")
        csv_export_path = input("Enter CSV export path: ")
        if not csv_export_path.endswith('/'):
            csv_export_path += '/'
        csv_filename = input("Enter CSV filename (without extension): ")
        
        # Styling configuration
        print("\nStyling Configuration:")
        plot_title = input("Enter plot title (e.g., 'Title of the plot'): ")
        x_axis_title = input("Enter X-axis title (e.g., 'Time (in ns)'): ")
        y_axis_title = input("Enter Y-axis title (e.g., 'Drain Outervoltage (in mV)'): ")
        y2_axis_title = input("Enter Y2-axis title (e.g., 'Max Lattice Temperature (in K)'): ")
        
        print("\nLegend Configuration:")
        legend_x = input("Enter legend X position (e.g., 0.0728291): ")
        legend_y = input("Enter legend Y position (e.g., 0.923963): ")
        
        print("\nExport Configuration:")
        png_export_path = input("Enter PNG export path (e.g., '/home2/shreenidha/tmp/plot_title.png'): ")
        
        cmds = []
        
        # Header
        cmds += [
            "################################################",
            "# Sentaurus Visual Console - Tcl version 8.6.6 #",
            "################################################",
            "# "
        ]
        
        # Load first file and create 1D plot
        first_version, first_node = nodes_data[0]
        first_filename = f"{plt_prefix}_{first_version}_{first_node}_des.plt"
        first_dataset = f"{plt_prefix}_{first_version}_{first_node}_des"
        
        cmds += [
            f"load_file {base_path}{first_filename}",
            "create_plot -1d",
            "select_plots {Plot_1}",
            "# Plot_1", "", "# Plot_1", "", f"# {first_dataset}"
        ]
        
        # Load remaining files
        for version, node_id in nodes_data[1:]:
            filename = f"{plt_prefix}_{version}_{node_id}_des.plt"
            dataset = f"{plt_prefix}_{version}_{node_id}_des"
            cmds += [
                f"load_file {base_path}{filename}",
                f"# {dataset}"
            ]
        
        # Create all datasets for curve creation
        all_datasets = " ".join(f"{plt_prefix}_{version}_{node_id}_des" for version, node_id in nodes_data)
        
        # Create curves for drain OuterVoltage (Y-axis) - all at once
        cmds += [
            f"create_curve -axisX time -axisY {{drain OuterVoltage}} -dataset {{{all_datasets}}} -plot Plot_1",
            f"# {' '.join(f'Curve_{i}' for i in range(1, len(nodes_data) + 1))}"
        ]
        
        # Create curves for Tmax (Y2-axis) - all at once
        tmax_curve_start = len(nodes_data) + 1
        tmax_curve_end = len(nodes_data) * 2
        cmds += [
            f"create_curve -axisX time -axisY2 Tmax -dataset {{{all_datasets}}} -plot Plot_1",
            f"# {' '.join(f'Curve_{i}' for i in range(tmax_curve_start, tmax_curve_end + 1))}"
        ]
        
        # Apply styling to Tmax curves (Y2-axis)
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ff8000", "#800080", "#008080"]
        for i, (version, node_id) in enumerate(nodes_data):
            curve_num = tmax_curve_start + i
            color = colors[i % len(colors)]
            cmds += [
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -line_style dash",
                "# 0",
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -line_width 2",
                "# 0",
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -color {color}",
                "# 0",
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -hide_legend",
                "# 0"
            ]
        
        # Apply styling to drain OuterVoltage curves (Y-axis)
        for i, (version, node_id) in enumerate(nodes_data):
            curve_num = i + 1
            cmds += [
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -line_width 2",
                "# 0"
            ]
        
        # Set axis properties
        cmds += [
            f"set_axis_prop -plot Plot_1 -axis y2 -title \"{y2_axis_title}\"",
            "# 0",
            f"set_axis_prop -plot Plot_1 -axis x -title \"{x_axis_title}\"",
            "# 0",
            f"set_axis_prop -plot Plot_1 -axis y -title \"{y_axis_title}\"",
            "# 0"
        ]
        
        # Set plot properties
        cmds += [
            f"set_plot_prop -plot {{Plot_1}} -title \"{plot_title}\"",
            "# 0",
            f"set_plot_prop -plot {{Plot_1}} -frame_width 2",
            "# 0"
        ]
        
        # Set legend position
        cmds += [
            f"set_legend_prop -plot Plot_1 -position {{{legend_x} {legend_y}}}",
            "# 0"
        ]
        
        # Export view as PNG
        cmds += [
            f"export_view {{{png_export_path}}} -format png",
            "# 0"
        ]
        
        # Move plot to origin
        cmds += [
            f"move_plot -plot Plot_1 -position {{0 0}}",
            "# 0"
        ]
        
        # Set custom labels for drain OuterVoltage curves
        for i, (version, node_id) in enumerate(nodes_data):
            curve_num = i + 1
            cmds += [
                f"set_curve_prop {{Curve_{curve_num}}} -plot Plot_1 -label \"drain OuterVoltage_{version}\"",
                "# 0"
            ]
        
        # Export curves to CSV
        all_curves = " ".join(f"Curve_{i}" for i in range(1, len(nodes_data) * 2 + 1))
        csv_full_path = f"{csv_export_path}{csv_filename}.csv"
        cmds += [
            f"export_curves {{{all_curves}}} -plot Plot_1 -filename {csv_full_path} -format csv",
            f"# {csv_full_path}"
        ]
        
        return cmds
        
    except (ValueError, KeyboardInterrupt):
        print("Input error or operation cancelled.")
        return []

# ──────────────────────────────────────────────
# Mode 3: Multiple Cutplane-Cutline-Parameter Sets (MODIFIED)
# ──────────────────────────────────────────────

def generate_mode3_commands():
    parameters = [
        "ConductionBandEnergy", "ConductionCurrentDensity", "DopingConcentration",
        "EffectiveIntrinsicDensity", "ElectricField", "ElectrostaticPotential",
        "EquilibriumPotential", "Impactionization", "IntrinsicDensity",
        "LatticeTemperature", "QuasiFermiPotential", "SpaceCharge",
        "ValenceBandEnergy", "eAlphaAvalanche", "eCurrentDensity", "eDensity",
        "eMobility", "eQuasiFermiPotential", "hAlphaAvalanche", "hCurrentDensity",
        "hDensity", "hMobility", "hQuasiFermiPotential"
    ]
    
    print("=" * 80)
    print("MODE 3: Unified 1D Plot for All Curves (Dynamic Sets/Parameters)")
    print("=" * 80)
    print("AVAILABLE PARAMETERS:")
    for p in parameters:
        print(f" • {p}")
    print("=" * 80)
    
    try:
        no_of_tdrs = int(input("Enter the number of TDRs for analysis: "))
        base_path = input("Enter base file path: ")
        if not base_path.endswith('/'):
            base_path += '/'
        
        file_prefix = input("Enter file prefix (e.g., n1278_I5_): ")
        
        # Get current value for new naming convention
        current_value = input("Enter current value for file naming: ")
        
        tdr_codes = []
        for i in range(no_of_tdrs):
            code = input(f"Enter last 2 digits of TDR-{i + 1} code (e.g., 00 for 0000): ")
            tdr_codes.append(format_tdr_code(code))
        
        cutplane_cutline_sets = []
        while True:
            print("\n--- New Set ---")
            cutplane_axis = input("Enter cutplane axis (x/y/z): ").lower()
            while cutplane_axis not in {'x', 'y', 'z'}:
                cutplane_axis = input("Invalid axis. Enter cutplane axis (x/y/z): ").lower()
            
            cutplane_position = input(f"Enter cutplane position on {cutplane_axis}-axis: ")
            
            cutline_axis = input("Enter cutline axis (x/y/z): ").lower()
            while cutline_axis not in {'x', 'y', 'z'}:
                cutline_axis = input("Invalid axis. Enter cutline axis (x/y/z): ").lower()
            
            if cutline_axis == cutplane_axis:
                print("Error: Cutplane and cutline cannot be on the same axis!")
                return []
            
            print(f"\nCutline positions for each TDR on {cutline_axis}-axis:")
            cutline_positions = []
            for code in tdr_codes:
                pos = input(f" Position for TDR {code}: ")
                cutline_positions.append(pos)
            
            # Modified to accept multiple parameters
            param_input = input("Enter parameter(s) for this set (comma-separated if multiple): ")
            param_list = parse_parameters(param_input)
            
            # Validate all parameters
            invalid_params = [p for p in param_list if p not in parameters]
            if invalid_params:
                print(f"Invalid parameter(s): {', '.join(invalid_params)}. Please choose from the available list.")
                continue
            
            cutplane_cutline_sets.append({
                'cutplane_axis': cutplane_axis,
                'cutplane_position': cutplane_position,
                'cutline_axis': cutline_axis,
                'cutline_positions': cutline_positions,
                'parameters': param_list  # Changed from 'parameter' to 'parameters'
            })
            
            more = input("Do you want to enter another set of cutplane and cutline? (yes/no): ").lower()
            if more not in ['yes', 'y']:
                break
        
        y_axis_type = input("Enter Y-axis type (linear/log) [default: log]: ").lower() or 'log'
        if y_axis_type not in {'linear', 'log'}:
            y_axis_type = 'log'
        
        csv_export_path = input("Enter CSV export path: ")
        if not csv_export_path.endswith('/'):
            csv_export_path += '/'
        
        csv_filename = input("Enter CSV filename (without extension): ")
        
        cmds = []
        plot_names = []
        
        # Process each set and parameter combination
        set_parameter_counter = 0
        for set_idx, cutset in enumerate(cutplane_cutline_sets, start=1):
            for param_idx, parameter in enumerate(cutset['parameters']):
                set_parameter_counter += 1
                
                cp_axis = cutset['cutplane_axis']
                cp_pos = cutset['cutplane_position']
                cl_axis = cutset['cutline_axis']
                cl_positions = cutset['cutline_positions']
                
                axis_x = get_axis_mapping(cp_axis, cl_axis)
                
                # Header for each set-parameter combination
                cmds += [
                    "################################################",
                    f"# Sentaurus Visual Console - Tcl version 8.6.6 #",
                    "################################################",
                    f"# --- Set {set_idx}, Parameter: {parameter} ---"
                ]
                
                # Load all TDRs with new naming convention: currentvalue_parameter_tdrcode
                for tdr_idx, code in enumerate(tdr_codes):
                    fname = f"{current_value}_{parameter}_{code}_des.tdr"
                    dset = f"{current_value}_{parameter}_{code}_des"
                    plot = f"Plot_{dset}"
                    
                    cmds += [
                        f"load_file {base_path}{fname} -fod",
                        f"create_plot -dataset {dset}",
                        f"select_plots {{{plot}}}",
                        f"# {plot}", "", f"# {plot}", "", f"# {dset}"
                    ]
                
                # Link all plots for this parameter
                first_plot = f"Plot_{current_value}_{parameter}_{tdr_codes[0]}_des"
                all_plots = " ".join(f"Plot_{current_value}_{parameter}_{code}_des" for code in tdr_codes)
                
                cmds += [
                    f"select_plots {{{first_plot}}}",
                    f"# {first_plot}",
                    f"select_plots {{{all_plots}}}",
                    f"# {all_plots}",
                    f"link_plots {{{all_plots}}}",
                    "# 1"
                ]
                
                # Set field property for the last plot
                last_plot = f"Plot_{current_value}_{parameter}_{tdr_codes[-1]}_des"
                last_dset = f"{current_value}_{parameter}_{tdr_codes[-1]}_des"
                
                cmds += [
                    f"set_field_prop {parameter} -plot {last_plot} -geom {last_dset} -show_bands",
                    "# 0"
                ]
                
                # Create cutplanes for all TDRs
                for code in tdr_codes:
                    plot = f"Plot_{current_value}_{parameter}_{code}_des"
                    cmds += [
                        f"select_plots {{{plot}}}",
                        f"# {plot}",
                        f"create_cutplane -plot {plot} -type {cp_axis} -at {cp_pos}",
                        f"# C{set_parameter_counter}({current_value}_{parameter}_{code}_des)"
                    ]
                
                # Create plots for cutplanes
                for code in tdr_codes:
                    cp_dset = f"C{set_parameter_counter}({current_value}_{parameter}_{code}_des)"
                    plot = f"Plot_{current_value}_{parameter}_{code}_des"
                    cmds += [
                        f"create_plot -dataset {cp_dset} -ref_plot {plot}",
                        f"select_plots {{Plot_{cp_dset}}}",
                        f"# Plot_{cp_dset}", "", f"# Plot_{cp_dset}"
                    ]
                
                # Create cutlines and 1D plot for this set-parameter combination
                for tdr_idx, code in enumerate(tdr_codes):
                    cp_plot = f"Plot_C{set_parameter_counter}({current_value}_{parameter}_{code}_des)"
                    cl_pos = cl_positions[tdr_idx]
                    cmds += [
                        f"select_plots {{{cp_plot}}}",
                        f"# {cp_plot}",
                        f"create_cutline -plot {cp_plot} -type {cl_axis} -at {cl_pos}",
                        f"# C1(C{set_parameter_counter}({current_value}_{parameter}_{code}_des))"
                    ]
                
                # Create 1D plot for this set-parameter combination
                plot1d_name = f"Plot_C1(C{set_parameter_counter}({current_value}_{parameter}_{tdr_codes[0]}_des))"
                plot_names.append(plot1d_name)
                first_cl_dset = f"C1(C{set_parameter_counter}({current_value}_{parameter}_{tdr_codes[0]}_des))"
                
                cmds += [
                    f"create_plot -dataset {first_cl_dset} -1d",
                    f"select_plots {{{plot1d_name}}}",
                    f"# {plot1d_name}", "", f"# {plot1d_name}"
                ]
                
                # Add curves for each TDR in this set-parameter combination
                for tdr_idx, code in enumerate(tdr_codes):
                    cl_dset = f"C1(C{set_parameter_counter}({current_value}_{parameter}_{code}_des))"
                    cmds += [
                        f"create_curve -axisX {axis_x} -axisY {parameter} -dataset {{{cl_dset}}} -plot {plot1d_name}",
                        f"# Curve_{tdr_idx+1}",
                        f"set_axis_prop -plot {plot1d_name} -axis y -type {y_axis_type}",
                        f"set_axis_prop -plot {plot1d_name} -axis x -range {{-0.9 9.0}}",
                        "# 0"
                    ]
                
                # Export curves to CSV for this set-parameter combination
                all_curve_names = " ".join(f"Curve_{i+1}" for i in range(len(tdr_codes)))
                csv_full_path = f"{csv_export_path}{csv_filename}_set{set_idx}_param{param_idx+1}_{parameter}.csv"
                
                cmds += [
                    f"select_plots {{{plot1d_name}}}",
                    f"# {plot1d_name}",
                    f"export_curves {{{all_curve_names}}} -plot {plot1d_name} -filename {csv_full_path} -format csv",
                    f"# {csv_full_path}"
                ]
        
        return cmds
        
    except (ValueError, KeyboardInterrupt):
        print("Input error or operation cancelled.")
        return []

# ──────────────────────────────────────────────
# Main Function
# ──────────────────────────────────────────────

def run_single_workflow():
    print("=" * 80)
    print("ENHANCED TCAD TCL COMMAND GENERATOR – Multi-Mode (Modified)")
    print("=" * 80)
    print("Available Modes:")
    print("1. Many nodes with user TDRs (with optional last TDR, flexible prefix)")
    print("2. Different nodes with PLT files")
    print("3. Multiple cutplane/cutline/parameter sets")
    print("=" * 80)
    print("\nMODIFICATIONS:")
    print("• Multiple parameters support (comma-separated) for Mode 1 & 3")
    print("• Simplified TDR code entry (last 2 digits only)")
    print("• File naming: currentvalue_parameter_tdrcode")
    print("• Fixed 2D plot generation for all parameter sets")
    print("=" * 80)
    
    try:
        mode = input("Select mode (1, 2, or 3): ")
        
        if mode == '1':
            commands = generate_mode1_commands()
        elif mode == '2':
            commands = generate_mode2_commands()
        elif mode == '3':
            commands = generate_mode3_commands()
        else:
            print("Invalid mode selection!")
            return False
        
        if not commands:
            print("No commands generated.")
            return False
        
        print("\n" + "=" * 80)
        print("GENERATED TCL COMMANDS")
        print("=" * 80)
        for cmd in commands:
            print(cmd)
        
        save = input("\nSave commands to .tcl file? (y/n): ").lower()
        if save == 'y':
            fname = input("Enter filename (e.g., script.tcl): ")
            try:
                with open(fname, 'w') as f:
                    for cmd in commands:
                        f.write(cmd + "\n")
                print(f"Commands saved to {fname}")
            except Exception as e:
                print(f"Error saving file: {e}")
        
        return True
        
    except (ValueError, KeyboardInterrupt):
        print("Operation cancelled.")
        return False

def main():
    print("=" * 80)
    print("WELCOME TO TCAD TCL COMMAND GENERATOR (MODIFIED)")
    print("=" * 80)
    
    while True:
        try:
            workflow_completed = run_single_workflow()
            if not workflow_completed:
                print("Workflow was not completed successfully.")
            
            print("\n" + "=" * 80)
            print("WORKFLOW COMPLETED")
            print("=" * 80)
            
            while True:
                continue_choice = input("Do you want to continue with another analysis? (yes/no): ").lower().strip()
                if continue_choice in ['yes', 'y']:
                    print("\n" + "=" * 50)
                    print("STARTING NEW WORKFLOW...")
                    print("=" * 50)
                    break
                elif continue_choice in ['no', 'n']:
                    print("\n" + "=" * 80)
                    print("THANK YOU FOR USING TCAD TCL COMMAND GENERATOR")
                    print("GOODBYE!")
                    print("=" * 80)
                    return
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    continue
                    
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user.")
            print("=" * 80)
            print("GOODBYE!")
            print("=" * 80)
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Restarting workflow...")
            continue

if __name__ == "__main__":
    main()