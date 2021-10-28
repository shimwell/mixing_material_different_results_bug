import openmc
import os


def run_simulation():
    # MATERIALS

    breeder_material = openmc.Material(1, "PbLi")  # Pb84.2Li15.8
    breeder_material.add_element('Pb', 84.2, percent_type='ao')
    breeder_material.add_element('Li', 15.8, percent_type='ao', enrichment=50.0, enrichment_target='Li6', enrichment_type='ao')  # 50% enriched
    breeder_material.set_density('atom/b-cm', 3.2720171e-2)  # around 11 g/cm3

    mats = openmc.Materials([breeder_material])

    # GEOMETRY

    # surfaces
    vessel_inner = openmc.Sphere(r=500)
    breeder_blanket_outer_surface = openmc.Sphere(r=600, boundary_type='vacuum')

    # cells
    inner_vessel_region = -vessel_inner
    inner_vessel_cell = openmc.Cell(region=inner_vessel_region)

    breeder_blanket_region = -breeder_blanket_outer_surface
    breeder_blanket_cell = openmc.Cell(region=breeder_blanket_region)
    breeder_blanket_cell.fill = breeder_material

    universe = openmc.Universe(cells=[inner_vessel_cell, breeder_blanket_cell])
    geom = openmc.Geometry(universe)

    # Instantiate a Settings object
    sett = openmc.Settings()
    sett.batches = 100
    sett.inactive = 0
    sett.particles = 5000
    sett.run_mode = 'fixed source'

    # Create a DT point source
    source = openmc.Source()
    source.space = openmc.stats.Point((0, 0, 0))
    source.angle = openmc.stats.Isotropic()
    source.energy = openmc.stats.Discrete([14e6], [1])
    sett.source = source

    tallies = openmc.Tallies()

    # added a cell tally for tritium production
    cell_filter = openmc.CellFilter(breeder_blanket_cell)
    tbr_tally = openmc.Tally(name='TBR')
    tbr_tally.filters = [cell_filter]
    tbr_tally.scores = ['(n,Xt)']  # Where X is a wildcard character, this catches any tritium production
    tallies.append(tbr_tally)

    # Run OpenMC!
    model = openmc.model.Model(geom, mats, sett, tallies)
    # exporting xml files and running with system due to issue number #1899
    # sp_filename = model.run()
    model.export_to_xml()
    os.system('openmc')

    # open the results file
    sp_filename = 'statepoint.100.h5'
    sp = openmc.StatePoint(sp_filename)

    # access the tally using pandas dataframes
    tbr_tally = sp.get_tally(name='TBR')
    df = tbr_tally.get_pandas_dataframe()

    tbr_tally_result = df['mean'].sum()
    tbr_tally_std_dev = df['std. dev.'].sum()

    # print results
    print(f'The tritium breeding ratio was found, TBR = {tbr_tally_result}')
    print(f'Standard deviation on the tbr tally is {tbr_tally_std_dev}')

    return tbr_tally_result, tbr_tally_std_dev


if __name__ == "__main__":
    values = []
    for i in range(10):
        value = run_simulation()
        values.append(value)

    print(values)

"""
typical values, variation is very small as materials.xml is in the same order?
(1.684769278870782, 0.0019266051133313604),
(1.6847692788707815, 0.001926605113326704),
(1.6847692788707826, 0.0019266051133371813),
(1.684769278870783, 0.001926605113327868),
(1.6847692788707815, 0.0019266051133255398),
(1.6847692788707838, 0.001926605113326704),
(1.68476927887078, 0.0019266051133336889),
(1.6847692788707804, 0.001926605113319719),
(1.6847692788707829, 0.0019266051133255398),
(1.6847692788707824, 0.0019266051133185547)

however switching the order of materials results all start with 1.6851
"""