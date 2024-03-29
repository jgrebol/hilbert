import numpy as np
from functools import reduce, lru_cache

########### CORE ESIpy ###########


def aromaticity(
    mol,
    mf,
    Smo,
    rings,
    mci_alg=None,
    d=None,
    calc=None,
    mci=False,
    av1245=False,
    num_threads=None,
):
    """Population analysis, localization and delocalization indices and aromaticity indicators.

    Args:

       mol: an instance of SCF class
          Mole class and helper functions to handle parameters and attributes for GTO integrals.

       mf: an instance of SCF class
          mf object holds all parameters to control SCF.

       Smo: list of matrices
          Atomic Overlap Matrices (AOMs) in the MO basis generated from the make_aoms() function.

       rings: list
          Contains a list of the indices of the atoms in the ring connectivity for the aromaticity calculations.

       calc: string
          Type of desired atom in molecule. Options are 'mulliken', lowdin', 'meta_lowdin', 'nao' and 'iao'.

       mci: boolean
          Whether to compute the MCI index.

       av1245: boolean
          Whether to compute the AV1245 (and AVmin) indies.

       num_threads: integer
          Number of threds required for the calculation.

    """

    symbols = [mol.atom_symbol(i) for i in range(mol.natm)]
    atom_numbers = [i + 1 for i in range(mol.natm)]

    if (
        mf.__class__.__name__ == "UHF"
        or mf.__class__.__name__ == "UKS"
        or mf.__class__.__name__ == "SymAdaptedUHF"
        or mf.__class__.__name__ == "SymAdaptedUKS"
    ):
        wf = "unrest"

    elif (
        mf.__class__.__name__ == "RHF"
        or mf.__class__.__name__ == "RKS"
        or mf.__class__.__name__ == "SymAdaptedRHF"
        or mf.__class__.__name__ == "SymAdaptedRKS"
        or mf.__class__.__name__ == "TDDFT"
    ):
        wf = "rest"

    else:
        wf = "no"
    ########### PRINTING THE OUTPUT ###########

    # Information from the calculation

    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print(" ** Localization & Delocalization Indices **  ")
    print(" ** For Hilbert Space Atomic Partitioning **  ")
    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print("  Application to Aromaticity Calculations\n  Joan Grebol")
    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print(" Number of Atoms:          {}".format(mol.natm))

    # UNRESTRICTED
    if wf == "unrest":
        print(
            " Occ. Mol. Orbitals:       {}({})".format(
                int(mf.mo_occ[0].sum()), int(mf.mo_occ[1].sum())
            )
        )
        print(" Wavefunction type:        uhf")

    # RESTRICTED
    elif wf == "rest":
        print(
            " Occ. Mol. Orbitals:       {}({})".format(
                int(mf.mo_occ.sum()), int(mf.mo_occ.sum())
            )
        )
        print(" Wavefunction type:        hf")

    # NATURAL ORBITALS
    else:
        print(
            " Occ. Mol. Orbitals:       {}({})".format(
                np.shape(Smo)[0], np.shape(Smo)[0]
            )
        )
        print(" Wavefunction type:        no")

    print(" Atomic partition:         {}".format(calc.upper()))
    print(" ------------------------------------------- ")
    print(" Method:                  ", mf.__class__.__name__)

    if "dft" in mf.__module__ and mf.xc is not None:
        print(" Functional:              ", mf.xc)

    print(" Basis set:               ", mol.basis.upper())
    print(" Total energy:          {:>13f}".format(mf.e_tot))
    print(" ------------------------------------------- ")

    if wf == "unrest":
        trace_alpha = np.sum([np.trace(matrix) for matrix in Smo[0]])
        trace_beta = np.sum([np.trace(matrix) for matrix in Smo[1]])
        print(" | Tr(alpha):    {:>13f}".format(trace_alpha))
        print(" | Tr(beta):     {:>13f}".format(trace_beta))
        print(" | Tr(total):    {:>13f}".format(trace_alpha + trace_beta))

    else:
        trace = np.sum([np.trace(matrix) for matrix in Smo])
        print(" | Tr(Enter):    {:.13f}".format(trace))
    print(" ------------------------------------------- ")

    # Checking the type of calculation and calling the function for each case

    # UNRESTRICTED
    if wf == "unrest":
        deloc_unrest(mol, Smo)
        arom_unrest(
            mol,
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )

    # RESTRICTED
    elif wf == "rest":
        deloc_rest(mol, Smo)
        arom_rest(
            mol,
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )

    # NATURAL ORBITALS
    else:
        deloc_no(mol, Smo)
        arom_no(
            mol,
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )


# AROMATICITY FROM LOADED AOMS
def aromaticity_from_aoms(
    Smo,
    rings,
    mci_alg=None,
    d=None,
    calc=None,
    wf=None,
    mci=False,
    av1245=False,
    num_threads=None,
):
    if wf is None:
        raise NameError("Please specify the type of wave function")

    ########### PRINTING THE OUTPUT ###########

    # Information from the calculation

    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print(" ** Localization & Delocalization Indices **  ")
    print(" ** For Hilbert Space Atomic Partitioning **  ")
    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print(
        "  Application to Aromaticity Calculations\n  Joan Grebol\n  See manual.pdf for citation of this program."
    )
    print(" -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ")
    print(" Number of Atoms:          {}".format(np.shape(Smo[0])[0]))

    # UNRESTRICTED
    if wf == "unrest":
        # print(' Occ. Mol. Orbitals:       {}({})'.format(int(np.shape(Smo[0])[1]),int(np.shape(Smo[1])[1])))
        print(" Wavefunction type:        uhf")

    # RESTRICTED
    if wf == "rest":
        print(" Wavefunction type:        hf")
        print(
            " Occ. Mol. Orbitals:       {}({})".format(
                int(np.shape(Smo)[1]), int(np.shape(Smo)[1])
            )
        )

    # NATURAL ORBITALS
    if wf != "unrest" and wf != "rest":
        print(" Wavefunction type:        no")

    if calc is not None:
        print(" Atomic partition:         {}".format(calc.upper()))
    if calc is None:
        print(" Atomic partition:         Not specified")

    print(" ------------------------------------------- ")
    print(" Method:            Not specified")
    print(" Basis set:         Not specified")
    print(" Total energy:      Not specified")
    print(" ------------------------------------------- ")

    if wf == "unrest":
        trace_alpha = np.sum([np.trace(matrix) for matrix in Smo[0]])
        trace_beta = np.sum([np.trace(matrix) for matrix in Smo[1]])
        print(" | Tr(alpha):    {:>13f}".format(trace_alpha))
        print(" | Tr(beta):     {:>13f}".format(trace_beta))
        print(" | Tr(total):    {:>13f}".format(trace_alpha + trace_beta))

    else:
        trace = np.sum([np.trace(matrix) for matrix in Smo])
        print(" | Tr(Enter):    {:.13f}".format(trace))
    print(" ------------------------------------------- ")

    # Checking the type of calculation and calling the function for each case

    # UNRESTRICTED
    if wf == "unrest":
        arom_unrest_from_aoms(
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )

    # RESTRICTED
    elif wf == "rest":
        arom_rest_from_aoms(
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )

    # NATURAL ORBITALS
    else:
        arom_no_from_aoms(
            Smo,
            rings,
            mci_alg=mci_alg,
            d=d,
            mci=mci,
            av1245=av1245,
            num_threads=num_threads,
        )


########### POPULATION STUDIES ###########

# POPULATION AND DELOCALIZAION UNRESTRICTED


def deloc_unrest(mol, Smo):
    # Getting the LIs and DIs
    atom_charges = mol.atom_charges()
    dis_alpha, dis_beta = [], []
    lis_alpha, lis_beta = [], []
    Nij_alpha, Nij_beta = [], []

    for i in range(mol.natm):
        li_alpha = np.trace(np.dot(Smo[0][i], Smo[0][i]))
        li_beta = np.trace(np.dot(Smo[1][i], Smo[1][i]))
        lis_alpha.append(li_alpha)
        lis_beta.append(li_beta)
        Nij_alpha.append(np.trace(Smo[0][i]))
        Nij_beta.append(np.trace(Smo[1][i]))

        for j in range(i + 1, mol.natm):
            if i != j:
                di_alpha = 2 * np.trace(np.dot(Smo[0][i], Smo[0][j]))
                di_beta = 2 * np.trace(np.dot(Smo[1][i], Smo[1][j]))
                dis_alpha.append(di_alpha)
                dis_beta.append(di_beta)

    print(
        " ----------------------------------------------------------------------------- "
    )
    print(
        " |  Atom     N(Sij)     Na(Sij)     Nb(Sij)     Lapl.      dloc_a     dloc_b  "
    )
    print(
        " ----------------------------------------------------------------------------- "
    )

    for i in range(mol.natm):
        print(
            " | {} {:>2d}   {:10.6f}  {:10.6f}  {:10.6f}   *******   {:8.4f}   {:8.4f} ".format(
                mol.atom_symbol(i),
                i + 1,
                Nij_alpha[i] + Nij_beta[i],
                Nij_alpha[i],
                Nij_beta[i],
                lis_alpha[i],
                lis_beta[i],
            )
        )
    print(
        " ----------------------------------------------------------------------------- "
    )
    print(
        " | TOT:   {:10.6f}  {:10.6f}  {:10.6f}   *******   {:8.4f}   {:8.4f}".format(
            sum(Nij_alpha) + sum(Nij_beta),
            sum(Nij_alpha),
            sum(Nij_beta),
            sum(lis_alpha),
            sum(lis_beta),
        )
    )
    print(
        " ----------------------------------------------------------------------------- "
    )
    print(" ------------------------------------------- ")
    print(" |    Pair         DI       DIaa      DIbb ")
    print(" ------------------------------------------- ")

    for i in range(mol.natm):
        for j in range(mol.natm):
            if i != j:
                print(
                    " | {} {}-{} {}  {:>9.4f} {:>9.4f} {:>9.4f}".format(
                        mol.atom_symbol(i),
                        str(i + 1).rjust(2),
                        mol.atom_symbol(j),
                        str(j + 1).rjust(2),
                        2
                        * (
                            np.trace(np.dot(Smo[0][i], Smo[0][j]))
                            + np.trace(np.dot(Smo[1][i], Smo[1][j]))
                        ),
                        2 * (np.trace(np.dot(Smo[0][i], Smo[0][j]))),
                        2 * (np.trace(np.dot(Smo[1][i], Smo[1][j]))),
                    )
                )
    print(" ------------------------------------------- ")
    print(
        " |    TOT:    {:>9.4f} {:>9.4f} {:>9.4f} ".format(
            sum(dis_alpha) + sum(dis_beta) + sum(lis_alpha) + sum(lis_beta),
            sum(dis_alpha) + sum(lis_alpha),
            sum(dis_beta) + sum(lis_beta),
        )
    )
    print(
        " |    LOC:    {:>9.4f} {:>9.4f} {:>9.4f} ".format(
            sum(lis_alpha) + sum(lis_beta), sum(lis_alpha), sum(lis_beta)
        )
    )
    print(
        " |  DELOC:    {:>9.4f} {:>9.4f} {:>9.4f} ".format(
            sum(dis_alpha) + sum(dis_beta), sum(dis_alpha), sum(dis_beta)
        )
    )
    print(" ------------------------------------------- ")


# POPULATION AND DELOCALIZATION RESTRICTED


def deloc_rest(mol, Smo):
    # Getting the LIs and DIs
    atom_charges = mol.atom_charges()
    dis = []
    lis = []
    Nij = []

    for i in range(mol.natm):
        li = 2 * np.trace(np.dot(Smo[i], Smo[i]))
        lis.append(li)
        Nij.append(2 * np.trace(Smo[i]))

        for j in range(i + 1, mol.natm):
            di = 4 * np.trace(np.dot(Smo[i], Smo[j]))
            dis.append(di)
    print(" ------------------------------------------------------- ")
    print(" |  Atom    N(Sij)         Lapl.       loc.       dloc. ")
    print(" ------------------------------------------------------- ")

    for i in range(mol.natm):
        if i != j:
            print(
                " | {} {:>2d}    {:10.6f}     *******   {:8.4f}   {:8.4f} ".format(
                    mol.atom_symbol(i), i + 1, Nij[i], lis[i], Nij[i] - lis[i]
                )
            )
    print(" ------------------------------------------------------- ")
    print(
        " | TOT:    {:10.6f}     *******   {:8.4f}   {:8.4f}".format(
            sum(Nij), sum(Nij) - sum(dis), sum(dis)
        )
    )
    print(" ------------------------------------------------------- ")

    print(" ------------------------ ")
    print(" |    Pair         DI ")
    print(" ------------------------ ")
    for i in range(mol.natm):
        for j in range(mol.natm):
            if i != j:
                print(
                    " | {} {}-{} {}   {:8.4f}".format(
                        mol.atom_symbol(i),
                        str(i + 1).rjust(2),
                        mol.atom_symbol(j),
                        str(j + 1).rjust(2),
                        4 * np.trace(np.dot(Smo[i], Smo[j])),
                    )
                )
    print(" ------------------------ ")
    print(" |   TOT:      {:8.4f} ".format(np.sum(dis) + np.sum(lis)))
    print(" |   LOC:      {:8.4f} ".format(np.sum(lis)))
    print(" | DELOC:      {:8.4f} ".format(np.sum(dis)))
    print(" ------------------------ ")


# POPULATION AND DELOCALIZATION NATURAL ORBITALS


def deloc_no(mol, Smo):
    # Generating Lis and DIs
    atom_charges = mol.atom_charges()
    dis = []
    lis = []
    Nij = []

    for i in range(mol.natm):
        li = np.trace(np.dot(Smo[i], Smo[i])) / 2
        lis.append(li)
        # lis = [np.trace(np.dot(Smo[i], Smo[j]))/2 for i in range(mol.natm) for j in range(mol.natm) if i != j]
        Nij.append(np.trace(Smo[i]))

        for j in range(i + 1, mol.natm):
            di = np.trace(np.dot(Smo[i], Smo[j]))
            dis.append(di)
    print(" ------------------------------------------------------- ")
    print(" |  Atom    N(Sij)         Lapl.       loc.       dloc. ")
    print(" ------------------------------------------------------- ")

    for i in range(mol.natm):
        print(
            " | {} {:>2d}    {:10.6f}     *******   {:8.4f}   {:8.4f} ".format(
                mol.atom_symbol(i), i + 1, Nij[i], lis[i], Nij[i] - lis[i]
            )
        )

    print(" ------------------------------------------------------- ")
    print(
        " | TOT:    {:10.6f}     *******   {:8.4f}   {:8.4f}".format(
            sum(Nij), sum(lis), sum(Nij) - sum(lis)
        )
    )
    print(" ------------------------------------------------------- ")

    print(" ------------------------ ")
    print(" |    Pair         DI ")
    print(" ------------------------ ")

    for i in range(mol.natm):
        for j in range(mol.natm):
            if i != j:
                print(
                    " | {} {}-{} {}   {:8.4f}".format(
                        mol.atom_symbol(i),
                        str(i + 1).rjust(2),
                        mol.atom_symbol(j),
                        str(j + 1).rjust(2),
                        np.trace(np.dot(Smo[i], Smo[j])),
                    )
                )
    print(" ------------------------ ")
    print(" |   TOT:      {:8.4f} ".format(np.sum(dis) + np.sum(lis)))
    print(" |   LOC:      {:8.4f} ".format(np.sum(lis)))
    print(" | DELOC:      {:8.4f} ".format(np.sum(dis)))
    print(" ------------------------ ")


########### AROMATICITY STUDIES ###########

# AROMATICITY UNRESTRICTED


def arom_unrest(mol, Smo, rings, mci_alg, d, mci=False, av1245=False, num_threads=1):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis_alpha = np.array(compute_pdi(ring, Smo[0])) / 2
            pdis_beta = np.array(compute_pdi(ring, Smo[1])) / 2

            print(
                " | PDI_alpha  {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_alpha[0],
                    pdis_alpha[1],
                    pdis_alpha[2],
                    pdis_alpha[3],
                )
            )
            print(
                " | PDI_beta   {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_beta[0],
                    pdis_beta[1],
                    pdis_beta[2],
                    pdis_beta[3],
                )
            )
            print(
                " | PDI_total  {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_alpha[0] + pdis_beta[0],
                    pdis_alpha[1] + pdis_beta[1],
                    pdis_alpha[2] + pdis_beta[2],
                    pdis_alpha[3] + pdis_beta[3],
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs_alpha = np.array(compute_av1245(ring, Smo[0]), dtype=object)
                avs_beta = np.array(compute_av1245(ring, Smo[1]), dtype=object)

                print(" |")
                print(" | *** AV1245_ALPHA ***")
                for j in range(len(ring)):
                    print(
                        " |  {} {} - {} {} - {} {} - {} {}  |  {:>9.4f}".format(
                            str(ring[j]).rjust(2),
                            mol.atom_symbol((ring[j] - 1) % len(ring)),
                            str(ring[(j + 1) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 1) % len(ring)] - 1),
                            str(ring[(j + 3) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 3) % len(ring)] - 1),
                            str(ring[(j + 4) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 4) % len(ring)] - 1),
                            np.array(avs_alpha[2][(ring[j] - 1) % len(ring)]) / 2,
                        )
                    )
                print(
                    " |   AV1245_alpha {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[0] / 2
                    )
                )
                print(
                    " |    AVmin_alpha {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[1] / 2
                    )
                )

                print(" |")
                print(" | *** AV1245_BETA ***")

                for j in range(len(ring)):
                    print(
                        " |  {} {} - {} {} - {} {} - {} {}  |  {:>9.4f}".format(
                            str(ring[j]).rjust(2),
                            mol.atom_symbol((ring[j] - 1) % len(ring)),
                            str(ring[(j + 1) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 1) % len(ring)] - 1),
                            str(ring[(j + 3) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 3) % len(ring)] - 1),
                            str(ring[(j + 4) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 4) % len(ring)] - 1),
                            np.array(avs_beta[2][(ring[j] - 1) % len(ring)]) / 2,
                        )
                    )
                print(
                    " |   AV1245_beta  {} =             {:>9.4f}".format(
                        ring_index + 1, avs_beta[0] / 2
                    )
                )
                print(
                    " |    AVmin_beta  {} =             {:>9.4f}".format(
                        ring_index + 1, avs_beta[1] / 2
                    )
                )
                print(" |")
                print(" | *** AV1245_TOTAL ***")
                print(
                    " |   AV1245       {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[0] / 2 + avs_beta[0] / 2
                    )
                )
                print(
                    " |    AVmin       {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[1] / 2 + avs_beta[1] / 2
                    )
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_alpha = compute_iring(ring, Smo[0])
        iring_beta = compute_iring(ring, Smo[1])
        iring_total = iring_alpha + iring_beta

        print(" | Iring_alpha  {} =  {:>6f}".format(ring_index + 1, iring_alpha))
        print(" | Iring_beta   {} =  {:>6f}".format(ring_index + 1, iring_beta))
        print(" | Iring_total  {} =  {:>6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )
        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_alpha = sequential_mci(ring, Smo[0])
                mci_beta = sequential_mci(ring, Smo[1])
                mci_total = mci_alpha + mci_beta
                end_mci = time.time()
                time_mci = end_mci - start_mci
                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI_alpha    {} =  {:>6f}".format(ring_index + 1, mci_alpha))
                print(" | MCI_beta     {} =  {:>6f}".format(ring_index + 1, mci_beta))
                print(" | MCI_total    {} =  {:>6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_alpha = multiprocessing_mci(
                    ring, Smo[0], num_threads, mci_alg=mci_alg, d=d
                )
                mci_beta = multiprocessing_mci(
                    ring, Smo[1], num_threads, mci_alg=mci_alg, d=d
                )
                mci_total = mci_alpha + mci_beta
                end_mci = time.time()
                time_mci = end_mci - start_mci
                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI_alpha    {} =  {:>6f}".format(ring_index + 1, mci_alpha))
                print(" | MCI_beta     {} =  {:>6f}".format(ring_index + 1, mci_beta))
                print(" | MCI_total    {} =  {:>6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )

            print(
                " ---------------------------------------------------------------------- "
            )


# AROMATICITY RESTRICTED


def arom_rest(mol, Smo, rings, mci_alg, d, mci=True, av1245=True, num_threads=1):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis = compute_pdi(ring, Smo)
            print(
                " | PDI  {} =             {:.4f} ( {:.4f} {:.4f} {:.4f} )".format(
                    ring_index + 1, pdis[0], pdis[1], pdis[2], pdis[3]
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs = compute_av1245(ring, Smo)

                for j in range(len(ring)):
                    print(
                        " |  {} {} - {} {} - {} {} - {} {}  |  {:>6.4f}".format(
                            str(ring[j]).rjust(2),
                            mol.atom_symbol((ring[j] - 1) % len(ring)),
                            str(ring[(j + 1) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 1) % len(ring)] - 1),
                            str(ring[(j + 3) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 3) % len(ring)] - 1),
                            str(ring[(j + 4) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 4) % len(ring)] - 1),
                            avs[2][(ring[j] - 1) % len(ring)],
                        )
                    )
                print(
                    " | AV1245 {} =             {:.4f}".format(ring_index + 1, avs[0])
                )
                print(
                    " |  AVmin {} =             {:.4f}".format(ring_index + 1, avs[1])
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_total = 2 * compute_iring(ring, Smo)
        print(" | Iring        {} =  {:>.6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )

        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_total = 2 * sequential_mci(ring, Smo)
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_total = 2 * multiprocessing_mci(
                    ring, Smo, num_threads, mci_alg=mci_alg, d=d
                )
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )
        print(
            " ---------------------------------------------------------------------- "
        )


# AROMATICITY NATURAL ORBITALS


def arom_no(mol, Smo, rings, mci_alg, d, mci=True, av1245=True, num_threads=1):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis = compute_pdi_no(ring, Smo)
            print(
                " | PDI  {} =             {:.4f} ( {:.4f} {:.4f} {:.4f} )".format(
                    ring_index + 1, pdis[0], pdis[1], pdis[2], pdis[3]
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs = compute_av1245_no(ring, Smo)

                for j in range(len(ring)):
                    print(
                        " |  {} {} - {} {} - {} {} - {} {}  |  {:>6.4f}".format(
                            str(ring[j]).rjust(2),
                            mol.atom_symbol((ring[j] - 1) % len(ring)),
                            str(ring[(j + 1) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 1) % len(ring)] - 1),
                            str(ring[(j + 3) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 3) % len(ring)] - 1),
                            str(ring[(j + 4) % len(ring)]).rjust(2),
                            mol.atom_symbol(ring[(j + 4) % len(ring)] - 1),
                            avs[2][(ring[j] - 1) % len(ring)] / 2,
                        )
                    )
                print(
                    " | AV1245 {} =             {:.4f}".format(
                        ring_index + 1, avs[0] / 2
                    )
                )
                print(
                    " |  AVmin {} =             {:.4f}".format(
                        ring_index + 1, avs[1] / 2
                    )
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_total = compute_iring_no(ring, Smo)

        print(" | Iring        {} =  {:>.6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )

        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_total = sequential_mci_no(ring, Smo)
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_total = multiprocessing_mci_no(
                    ring, Smo, num_threads, mci_alg=mci_alg, d=d
                )
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )
        print(
            " ---------------------------------------------------------------------- "
        )


def arom_unrest_from_aoms(
    Smo, rings, mci_alg, d, mci=False, av1245=False, num_threads=1
):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis_alpha = np.array(compute_pdi(ring, Smo[0])) / 2
            pdis_beta = np.array(compute_pdi(ring, Smo[1])) / 2

            print(
                " | PDI_alpha  {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_alpha[0],
                    pdis_alpha[1],
                    pdis_alpha[2],
                    pdis_alpha[3],
                )
            )
            print(
                " | PDI_beta   {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_beta[0],
                    pdis_beta[1],
                    pdis_beta[2],
                    pdis_beta[3],
                )
            )
            print(
                " | PDI_total  {} =         {:>9.4f} ( {:>9.4f} {:>9.4f} {:>9.4f} )".format(
                    ring_index + 1,
                    pdis_alpha[0] + pdis_beta[0],
                    pdis_alpha[1] + pdis_beta[1],
                    pdis_alpha[2] + pdis_beta[2],
                    pdis_alpha[3] + pdis_beta[3],
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs_alpha = np.array(compute_av1245(ring, Smo[0]), dtype=object)
                avs_beta = np.array(compute_av1245(ring, Smo[1]), dtype=object)

                def av1245_pairs(arr):
                    return [
                        (
                            arr[i % len(arr)],
                            arr[(i + 1) % len(arr)],
                            arr[(i + 3) % len(arr)],
                            arr[(i + 4) % len(arr)],
                        )
                        for i in range(len(arr))
                    ]

                av_order = av1245_pairs(ring)

                print(" |")
                print(" | *** AV1245_ALPHA ***")
                for j in range(len(ring)):
                    print(
                        " |  A {} - A {} - A {} - A {}  |  {:>9.4f}".format(
                            str(av_order[j][0]).rjust(2),
                            str(av_order[j][1]).rjust(2),
                            str(av_order[j][2]).rjust(2),
                            str(av_order[j][3]).rjust(2),
                            np.array(avs_alpha[2][(ring[j] - 1) % len(ring)]) / 2,
                        )
                    )
                print(
                    " |   AV1245_alpha {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[0] / 2
                    )
                )
                print(
                    " |    AVmin_alpha {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[1] / 2
                    )
                )

                print(" |")
                print(" | *** AV1245_BETA ***")

                for j in range(len(ring)):
                    print(
                        " |  A {} - A {} - A {} - A {}  |  {:>9.4f}".format(
                            str(av_order[j][0]).rjust(2),
                            str(av_order[j][1]).rjust(2),
                            str(av_order[j][2]).rjust(2),
                            str(av_order[j][3]).rjust(2),
                            np.array(avs_beta[2][(ring[j] - 1) % len(ring)]) / 2,
                        )
                    )
                print(
                    " |   AV1245_beta  {} =             {:>9.4f}".format(
                        ring_index + 1, avs_beta[0] / 2
                    )
                )
                print(
                    " |    AVmin_beta  {} =             {:>9.4f}".format(
                        ring_index + 1, avs_beta[1] / 2
                    )
                )
                print(" |")
                print(" | *** AV1245_TOTAL ***")
                print(
                    " |   AV1245       {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[0] / 2 + avs_beta[0] / 2
                    )
                )
                print(
                    " |    AVmin       {} =             {:>9.4f}".format(
                        ring_index + 1, avs_alpha[1] / 2 + avs_beta[1] / 2
                    )
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_alpha = compute_iring(ring, Smo[0])
        iring_beta = compute_iring(ring, Smo[1])
        iring_total = iring_alpha + iring_beta

        print(" | Iring_alpha  {} =  {:>6f}".format(ring_index + 1, iring_alpha))
        print(" | Iring_beta   {} =  {:>6f}".format(ring_index + 1, iring_beta))
        print(" | Iring_total  {} =  {:>6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )
        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_alpha = sequential_mci(ring, Smo[0])
                mci_beta = sequential_mci(ring, Smo[1])
                mci_total = mci_alpha + mci_beta
                end_mci = time.time()
                time_mci = end_mci - start_mci
                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI_alpha    {} =  {:>6f}".format(ring_index + 1, mci_alpha))
                print(" | MCI_beta     {} =  {:>6f}".format(ring_index + 1, mci_beta))
                print(" | MCI_total    {} =  {:>6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_alpha = multiprocessing_mci(
                    ring, Smo[0], num_threads, mci_alg=mci_alg, d=d
                )
                mci_beta = multiprocessing_mci(
                    ring, Smo[1], num_threads, mci_alg=mci_alg, d=d
                )
                mci_total = mci_alpha + mci_beta
                end_mci = time.time()
                time_mci = end_mci - start_mci
                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI_alpha    {} =  {:>6f}".format(ring_index + 1, mci_alpha))
                print(" | MCI_beta     {} =  {:>6f}".format(ring_index + 1, mci_beta))
                print(" | MCI_total    {} =  {:>6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )
            print(
                " ---------------------------------------------------------------------- "
            )


# AROMATICITY RESTRICTED


def arom_rest_from_aoms(Smo, rings, mci_alg, d, mci=True, av1245=True, num_threads=1):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis = compute_pdi(ring, Smo)
            print(
                " | PDI  {} =             {:.4f} ( {:.4f} {:.4f} {:.4f} )".format(
                    ring_index + 1, pdis[0], pdis[1], pdis[2], pdis[3]
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs = 2 * compute_av1245(ring, Smo)

                def av1245_pairs(arr):
                    return [
                        (
                            arr[i % len(arr)],
                            arr[(i + 1) % len(arr)],
                            arr[(i + 3) % len(arr)],
                            arr[(i + 4) % len(arr)],
                        )
                        for i in range(len(arr))
                    ]

                av_order = av1245_pairs(ring)

                for j in range(len(ring)):
                    print(
                        " |  A {} - A {} - A {} - A {}  |  {:>6.4f}".format(
                            str(av_order[j][0]).rjust(2),
                            str(av_order[j][1]).rjust(2),
                            str(av_order[j][2]).rjust(2),
                            str(av_order[j][3]).rjust(2),
                            avs[2][(ring[j] - 1) % len(ring)],
                        )
                    )
                print(
                    " | AV1245 {} =             {:.4f}".format(ring_index + 1, avs[0])
                )
                print(
                    " |  AVmin {} =             {:.4f}".format(ring_index + 1, avs[1])
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_total = 2 * compute_iring(ring, Smo)
        print(" | Iring        {} =  {:>.6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )

        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_total = 2 * sequential_mci(ring, Smo)
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_total = 2 * multiprocessing_mci(
                    ring, Smo, num_threads, mci_alg=mci_alg, d=d
                )
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )
        print(
            " ---------------------------------------------------------------------- "
        )


# AROMATICITY NATURAL ORBITALS


def arom_no_from_aoms(Smo, rings, mci_alg, d, mci=True, av1245=True, num_threads=1):
    print(" ----------------------------------------------------------------------")
    print(" | Aromaticity indices - PDI [CEJ 9, 400 (2003)]")
    print(" |                     Iring [PCCP 2, 3381 (2000)]")
    print(" |                    AV1245 [PCCP 18, 11839 (2016)]")
    print(" |                    AVmin  [JPCC 121, 27118 (2017)]")
    print(" |                           [PCCP 20, 2787 (2018)]")
    print(" |  For a recent review see: [CSR 44, 6434 (2015)]")
    print(" ----------------------------------------------------------------------")

    # Checking if the list rings is contains more than one ring to analyze

    if not isinstance(rings[0], list):
        rings = [rings]

    # Looping through each of the rings

    for ring_index, ring in enumerate(rings):
        print(" ----------------------------------------------------------------------")
        print(" |")
        print(
            " | Ring  {} ({}):   {}".format(
                ring_index + 1, len(ring), "  ".join(str(num) for num in ring)
            )
        )
        print(" ----------------------------------------------------------------------")

        # Printing the PDI

        if len(ring) != 6:
            print(" |   PDI could not be calculated as the number of centers is not 6")

        else:
            pdis = compute_pdi_no(ring, Smo)
            print(
                " | PDI  {} =             {:.4f} ( {:.4f} {:.4f} {:.4f} )".format(
                    ring_index + 1, pdis[0], pdis[1], pdis[2], pdis[3]
                )
            )
            print(
                " ---------------------------------------------------------------------- "
            )

        if av1245 == True:
            if len(ring) < 6:
                print(
                    " | AV1245 could not be calculated as the number of centers is smaller than 6 "
                )

            else:
                avs = compute_av1245_no(ring, Smo)

                def av1245_pairs(arr):
                    return [
                        (
                            arr[i % len(arr)],
                            arr[(i + 1) % len(arr)],
                            arr[(i + 3) % len(arr)],
                            arr[(i + 4) % len(arr)],
                        )
                        for i in range(len(arr))
                    ]

                av_order = av1245_pairs(ring)

                for j in range(len(ring)):
                    print(
                        " |  A {} - A {} - A {} - A {}  |  {:>6.4f}".format(
                            str(av_order[j][0]).rjust(2),
                            str(av_order[j][1]).rjust(2),
                            str(av_order[j][2]).rjust(2),
                            str(av_order[j][3]).rjust(2),
                            avs[2][(ring[j] - 1) % len(ring)] / 2,
                        )
                    )
                print(
                    " | AV1245 {} =             {:.4f}".format(
                        ring_index + 1, avs[0] / 2
                    )
                )
                print(
                    " |  AVmin {} =             {:.4f}".format(
                        ring_index + 1, avs[1] / 2
                    )
                )
                print(
                    " ---------------------------------------------------------------------- "
                )

        iring_total = compute_iring_no(ring, Smo)

        print(" | Iring        {} =  {:>.6f}".format(ring_index + 1, iring_total))

        if iring_total < 0:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, -(np.abs(iring_total) ** (1 / len(ring)))
                )
            )

        else:
            print(
                " | Iring**(1/n) {} =  {:>.6f}".format(
                    ring_index + 1, iring_total ** (1 / len(ring))
                )
            )

        print(
            " ---------------------------------------------------------------------- "
        )

        if mci == True:
            import time

            if num_threads is None:
                num_threads = 1

            # SINGLE-CORE
            if num_threads == 1:
                print(" | The program will use MCI2 algorithm")
                start_mci = time.time()
                mci_total = sequential_mci_no(ring, Smo)
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using 1 core took {:.4f} seconds".format(
                        time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            # MULTI-CORE
            else:
                print(" | The program will use MCI1 algorithm")
                start_mci = time.time()
                mci_total = multiprocessing_mci_no(
                    ring, Smo, num_threads, mci_alg=mci_alg, d=d
                )
                end_mci = time.time()
                time_mci = end_mci - start_mci

                print(
                    " | The MCI calculation using {} cores took {:.4f} seconds".format(
                        num_threads, time_mci
                    )
                )
                print(" | MCI          {} =  {:.6f}".format(ring_index + 1, mci_total))

            if mci_total < 0:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, -((np.abs(mci_total)) ** (1 / len(ring)))
                    )
                )

            else:
                print(
                    " | MCI**(1/n)   {} =  {:>6f}".format(
                        ring_index + 1, mci_total ** (1 / len(ring))
                    )
                )
        print(
            " ---------------------------------------------------------------------- "
        )


########### COMPUTATION OF THE AROMATICITY DESCRIPTORS ###########

########## Iring ###########

# Computing the Iring (Restricted and Unrestricted)


def compute_iring(arr, Smo):
    product = np.identity(Smo[0].shape[0])

    for i in arr:
        product = np.dot(product, Smo[i - 1])

    iring = 2 ** (len(arr) - 1) * np.trace(product)

    return iring


# Computing the Iring (Natural Orbitals)


def compute_iring_no(arr, Smo):
    product = np.identity(Smo[0].shape[0])

    for i in arr:
        product = np.dot(product, Smo[i - 1])

    return np.trace(product)


########### MCI ###########

# Generating all the (n-1)!/2 non-cyclic permutations


def unique_permutations(nums):
    from itertools import permutations

    perm_set = set()

    for perm in permutations(nums[:-1]):
        if perm not in perm_set and perm[::-1] not in perm_set:
            perm_set.add(perm)

    perm_final = set()

    for perm in perm_set:
        perm_final.add(perm + (nums[-1],))

    return list(perm_final)


# MCI algorithm that does not store all the permutations (MCI2) (Restricted and Unrestricted)


def sequential_mci(arr, Smo):
    mci_value = 0

    def generate_permutations(n, a, b, Smo):
        nonlocal mci_value

        if n == 1:
           if a[0] > a[-1]:
            a = a + [b]
            mci_value += compute_iring(a, Smo)

        else:
            for i in range(n - 1):
                generate_permutations(n - 1, a, b, Smo)

                if n % 2 == 0:
                    a[i], a[n - 1] = a[n - 1], a[i]

                else:
                    a[0], a[n - 1] = a[n - 1], a[0]
            generate_permutations(n - 1, a, b, Smo)

    generate_permutations(len(arr) - 1, arr[:-1], arr[-1], Smo)

    return mci_value


# MCI algorithm that does not store all the permutations (MCI2) (Natural Orbitals)


def sequential_mci_no(arr, Smo):
    mci_value = 0

    def generate_permutations(n, a, b, Smo):
        nonlocal mci_value
        iring = 0

        if n == 1 and a[0] > a[-1]:
            a = a + [b]
            mci_value += compute_iring_no(a, Smo)

        else:
            for i in range(n - 1):
                generate_permutations(n - 1, a, b, Smo)

                if n % 2 == 0:
                    a[i], a[n - 1] = a[n - 1], a[i]

                else:
                    a[0], a[n - 1] = a[n - 1], a[0]
            generate_permutations(n - 1, a, b, Smo)

    generate_permutations(len(arr) - 1, arr[:-1], arr[-1], Smo)

    return mci_value


### MCI APPROXIMATIONS ###

### MCI ALG 1 ###
# All the permutations that have a maximum distance between vertices
# of at max distance d


def hamilton_mci_alg_1(n, d):
    import math

    def dfs(path):
        if len(path) == n:
            val = min(abs(path[0] - path[-1]), n - abs(path[0] - path[-1]))

            if val <= d:
                cycles.append(path)

        for v in range(n):
            if v not in path:
                val = min(abs(v - path[-1]), n - abs(v - path[-1]))

                if val <= d:
                    dfs(path + [v])

    cycles = []
    dfs([0])
    return cycles


### MCI ALG 2 ###
# All the permutations that have at ONLY one pair of vertices
# separated by a distance d


def hamilton_mci_alg_2(n, d):
    import math

    def dfs(path):
        if len(path) == n:
            max = 0
            for i in range(n - 1):
                val = min(abs(path[i] - path[i + 1]), n - abs(path[i] - path[i + 1]))
                if val > max:
                    max = val
            val = min(abs(path[0] - path[-1]), n - abs(path[0] - path[-1]))
            if val > max:
                max = val
            if max == d:
                cycles.append(path)
        for v in range(n):
            if v not in path:
                val = min(abs(v - path[-1]), n - abs(v - path[-1]))
                if val <= d:
                    dfs(path + [v])

    cycles = []
    dfs([0])
    return cycles


### MCI ALG 3 ###
# Maximum distance between consecutive vertices set do d, and excluding
# all permutations where there is at least two vertices separated by an
# even distance (ONLY ODD DISTANCES)


def hamilton_mci_alg_3(n, d):
    import math

    def dfs(path):
        if len(path) == n:
            val = min(abs(path[0] - path[-1]), n - abs(path[0] - path[-1]))

            if val <= d and val % 2 != 0:
                cycles.append(path)

        for v in range(n):
            if v not in path:
                val = min(abs(v - path[-1]), n - abs(v - path[-1]))

                if val <= d and val % 2 != 0:
                    dfs(path + [v])

    cycles = []
    dfs([0])
    return cycles


### MCI ALG 4 ###
# Maximum distance between consecutive vertices set do d, and excluding
# all permutations where there is at least two vertices separated by an
# even distance (ONLY ODD DISTANCES).
# Not very useful because for even n value, it is impossible to make
# hamilton cycles with only even jumps between vertices...
# only if n is odd there are such hamilton cycles


def hamilton_mci_alg_4(n, d):
    import math

    def dfs(path):
        if len(path) == n:
            cycles.append(path)

        for v in range(n):
            if v not in path:
                val = min(abs(v - path[-1]), n - abs(v - path[-1]))

                if val <= d and val % 2 == 0:
                    dfs(path + [v])

    cycles = []
    dfs([0])
    return cycles


# MCI algorithm that splits the job into different threads (MCI1) (Restricted and Unrestricted)


def multiprocessing_mci(arr, Smo, num_threads, mci_alg, d):
    import multiprocessing as mp
    from functools import partial

    a, b, count = 0, 0, 0
    # Setting the default values if not specified
    if mci_alg is None:
        mci_alg = 0
    if d is None:
        d = 1

    if mci_alg == 0:
        print(f" | Using MCI's standard multiprocessing algorithm")
    if mci_alg != 0:
        print(f" | Using MCI's approximation {mci_alg} for d={d}")

    permutations = []
    if mci_alg == 0:
        permutations = unique_permutations(arr)

    elif mci_alg == 1:
        cycles = hamilton_mci_alg_1(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 2:
        cycles = hamilton_mci_alg_2(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 3:
        cycles = hamilton_mci_alg_3(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 4:
        cycles = hamilton_mci_alg_4(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    print(" | The total number of permutations is ", len(permutations))

    # Create a pool of workers
    pool = mp.Pool(processes=num_threads)

    dumb = partial(compute_iring, Smo=Smo)
    results = pool.map(dumb, permutations)

    trace = sum(results)

    # if mci_alg == 0:
    #   trace = trace * 2

    return trace


# MCI algorithm that splits the job into different threads (MCI1) (Natural Orbitals)


def multiprocessing_mci_no(arr, Smo, num_threads, mci_alg, d):
    import multiprocessing as mp
    from functools import partial

    if mci_alg is None:
        mci_alg = 0
    if d is None:
        d = 1

    if mci_alg == 0:
        print(f" | Using MCI's standard multiprocessing algorithm")
    if mci_alg != 0:
        print(f" | Using MCI's approximation {mci_alg} for d={d}")

    # If not specified, it will compute the exact MCI
    permutations = []
    if mci_alg == 0:
        permutations = unique_permutations(arr)

    elif mci_alg == 1:
        cycles = hamilton_mci_alg_1(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 2:
        cycles = hamilton_mci_alg_2(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 3:
        cycles = hamilton_mci_alg_3(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    elif mci_alg == 4:
        cycles = hamilton_mci_alg_4(len(arr), d)
        for perm in cycles:
            permutation = [arr[i] for i in perm]
            permutations.append(permutation)

    # Create a pool of workers
    pool = mp.Pool(processes=num_threads)

    dumb = partial(compute_iring_no, Smo=Smo)
    results = pool.map(dumb, permutations)

    trace = sum(results)

    return trace


########### AV1245 ###########

# Calculation of the AV1245 index (Restricted and Unrestricted)


def compute_av1245(arr, Smo):
    def av1245_pairs(arr):
        return [
            (
                arr[i % len(arr)],
                arr[(i + 1) % len(arr)],
                arr[(i + 3) % len(arr)],
                arr[(i + 4) % len(arr)],
            )
            for i in range(len(arr))
        ]

    min_product, av1245_value, avmin_value = 0, 0, 0
    val = 0
    product = 0
    products = []

    for cp in av1245_pairs(arr):
        product = sequential_mci(list(cp), Smo) * 2 / 3
        val += product
        products.append(1000 * product)

    min_product = min(products, key=abs)
    av1245_value = np.mean(products)
    avmin_value = min_product

    return [av1245_value, avmin_value, products]


# Calculation of the AV1245 index (Natural Orbitals)


def compute_av1245_no(arr, Smo):
    def av1245_pairs(arr):
        return [
            (
                arr[i % len(arr)],
                arr[(i + 1) % len(arr)],
                arr[(i + 3) % len(arr)],
                arr[(i + 4) % len(arr)],
            )
            for i in range(len(arr))
        ]

    min_product, av1245_value, avmin_value = 0, 0, 0
    val = 0
    product = 0
    products = []

    for cp in av1245_pairs(arr):
        product = sequential_mci_no(list(cp), Smo) * 2 / 3
        val += product
        products.append(1000 * product)

    min_product = min(products, key=abs)
    av1245_value = np.mean(products)
    avmin_value = min_product

    return [av1245_value, avmin_value, products]


########### PDI ###########

# Calculation of the PDI (Restricted and Unrestricted)


def compute_pdi(arr, Smo):
    if len(arr) == 6:
        pdi_a = 4 * np.trace(np.dot(Smo[arr[0] - 1], Smo[arr[3] - 1]))
        pdi_b = 4 * np.trace(np.dot(Smo[arr[1] - 1], Smo[arr[4] - 1]))
        pdi_c = 4 * np.trace(np.dot(Smo[arr[2] - 1], Smo[arr[5] - 1]))
        pdi_value = (pdi_a + pdi_b + pdi_c) / 3

        return [pdi_value, pdi_a, pdi_b, pdi_c]

    else:
        return None


# Calculation of the PDI (Natural Orbitals)


def compute_pdi_no(arr, Smo):
    if len(arr) == 6:
        pdi_a = np.trace(np.dot(Smo[arr[0] - 1], Smo[arr[3] - 1]))
        pdi_b = np.trace(np.dot(Smo[arr[1] - 1], Smo[arr[4] - 1]))
        pdi_c = np.trace(np.dot(Smo[arr[2] - 1], Smo[arr[5] - 1]))
        pdi_value = (pdi_a + pdi_b + pdi_c) / 3

        return [pdi_value, pdi_a, pdi_b, pdi_c]

    else:
        return None


########### ATOMIC OVERLAP MATRICES ###########

# Generating the Atomic Overlap Matrices


def make_aoms(mol, mf, calc=None):
    from pyscf import lo
    import numpy as np
    import os

    # UNRESTRICTED
    print(mf.__class__.__name__)
    if (
        mf.__class__.__name__ == "UHF"
        or mf.__class__.__name__ == "UKS"
        or mf.__class__.__name__ == "SymAdaptedUHF"
        or mf.__class__.__name__ == "SymAdaptedUKS"
    ):
        # Getting specific information

        natom = mol.natm
        nbas = mol.nao
        S = mf.get_ovlp()
        nocc_alpha = mf.mo_occ[0].astype(int)
        nocc_beta = mf.mo_occ[1].astype(int)
        occ_coeff_alpha = mf.mo_coeff[0][:, : nocc_alpha.sum()]
        occ_coeff_beta = mf.mo_coeff[0][:, : nocc_beta.sum()]

        # Building the Atomic Overlap Matrices

        Smo_alpha = []
        Smo_beta = []

        if calc == "lowdin" or calc == "meta_lowdin":
            U_inv = lo.orth_ao(mf, calc, pre_orth_ao="ANO")
            U = np.linalg.inv(U_inv)

            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR_alpha = np.linalg.multi_dot((occ_coeff_alpha.T, U.T, eta[i]))
                SCR_beta = np.linalg.multi_dot((occ_coeff_beta.T, U.T, eta[i]))
                Smo_alpha.append(np.dot(SCR_alpha, SCR_alpha.T))
                Smo_beta.append(np.dot(SCR_beta, SCR_beta.T))

        elif calc == "nao":
            U_inv = nao(mol, mf, s=None, restore=True)
            U = np.linalg.inv(U_inv)

            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR_alpha = np.linalg.multi_dot((occ_coeff_alpha.T, U.T, eta[i]))
                SCR_beta = np.linalg.multi_dot((occ_coeff_beta.T, U.T, eta[i]))
                Smo_alpha.append(np.dot(SCR_alpha, SCR_alpha.T))
                Smo_beta.append(np.dot(SCR_beta, SCR_beta.T))

        # Special case IAO
        elif calc == "iao":
            U_alpha_iao_nonortho = lo.iao.iao(mol, occ_coeff_alpha)
            U_beta_iao_nonortho = lo.iao.iao(mol, occ_coeff_beta)
            U_alpha_inv = np.dot(
                U_alpha_iao_nonortho,
                lo.orth.lowdin(
                    np.linalg.multi_dot(
                        (U_alpha_iao_nonortho.T, S, U_alpha_iao_nonortho)
                    )
                ),
            )
            U_beta_inv = np.dot(
                U_beta_iao_nonortho,
                lo.orth.lowdin(
                    np.linalg.multi_dot((U_beta_iao_nonortho.T, S, U_beta_iao_nonortho))
                ),
            )
            U_alpha = np.dot(S, U_alpha_inv)
            U_beta = np.dot(S, U_beta_inv)
            pmol = lo.iao.reference_mol(mol)
            nbas_iao = pmol.nao

            eta = [np.zeros((pmol.nao, pmol.nao)) for i in range(pmol.natm)]
            for i in range(pmol.natm):
                start = pmol.aoslice_by_atom()[i, -2]
                end = pmol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(pmol.natm):
                SCR_alpha = np.linalg.multi_dot((occ_coeff_alpha.T, U_alpha, eta[i]))
                SCR_beta = np.linalg.multi_dot((occ_coeff_beta.T, U_beta, eta[i]))
                Smo_alpha.append(np.dot(SCR_alpha, SCR_alpha.T))
                Smo_beta.append(np.dot(SCR_beta, SCR_beta.T))

        # Special case plain Mulliken
        elif calc == "mulliken":
            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR_alpha = np.linalg.multi_dot(
                    (occ_coeff_alpha.T, S, eta[i], occ_coeff_alpha)
                )
                SCR_beta = np.linalg.multi_dot(
                    (occ_coeff_beta.T, S, eta[i], occ_coeff_beta)
                )
                Smo_alpha.append(SCR_alpha)
                Smo_beta.append(SCR_beta)

        else:
            raise NameError("Hilbert-space scheme not available")

        return [Smo_alpha, Smo_beta]

    # RESTRICTED

    elif (
        mf.__class__.__name__ == "RHF"
        or mf.__class__.__name__ == "RKS"
        or mf.__class__.__name__ == "SymAdaptedRHF"
        or mf.__class__.__name__ == "SymAdaptedRKS"
        or mf.__class__.__name__ == "TDDFT"
    ):
        # Getting specific information

        natom = mol.natm
        nbas = mol.nao
        S = mf.get_ovlp()
        occ_coeff = mf.mo_coeff[:, mf.mo_occ > 0]

        # Building the Atomic Overlap Matrices

        Smo = []

        if calc == "lowdin" or calc == "meta_lowdin":
            U_inv = lo.orth_ao(mf, calc, pre_orth_ao="ANO")
            U = np.linalg.inv(U_inv)

            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, U.T, eta[i]))
                Smo.append(np.dot(SCR, SCR.T))

        elif calc == "nao":
            U_inv = nao(mol, mf, s=None, restore=True)
            U = np.linalg.inv(U_inv)

            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, U.T, eta[i]))
                Smo.append(np.dot(SCR, SCR.T))

        # Special case IAO
        elif calc == "iao":
            U_iao_nonortho = lo.iao.iao(mol, occ_coeff)
            U_inv = np.dot(
                U_iao_nonortho,
                lo.orth.lowdin(
                    np.linalg.multi_dot((U_iao_nonortho.T, S, U_iao_nonortho))
                ),
            )
            U = np.dot(S, U_inv)
            pmol = lo.iao.reference_mol(mol)
            nbas_iao = pmol.nao

            eta = [np.zeros((pmol.nao, pmol.nao)) for i in range(pmol.natm)]
            for i in range(pmol.natm):
                start = pmol.aoslice_by_atom()[i, -2]
                end = pmol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(pmol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, U, eta[i]))
                Smo.append(np.dot(SCR, SCR.T))

        # Special case plain Mulliken
        elif calc == "mulliken":
            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, S, eta[i], occ_coeff))
                Smo.append(SCR)

        else:
            raise NameError("Hilbert-space scheme not available")

        return Smo

    # NATURAL ORBITALS
    else:
        Smo = []
        natom = mol.natm
        threshold = 1e-5
        nbas = mol.nao
        S = mol.intor("int1e_ovlp")

        from pyscf import mcscf

        N_all, occ_coeff_all = mcscf.addons.make_natural_orbitals(
            mf
        )  # Get the occupancies vector for all orbitals
        N = np.array(
            [num for num in N_all if num >= threshold]
        )  # Filter the occupancies vector to get only the occupied orbitals
        occ_coeff = occ_coeff_all[
            :, : len(N)
        ]  # Filter the coefficients matrix to get only the occupied orbitals

        # Orthogonality test
        #   print(np.linalg.multi_dot((occ_coeff.T, S, occ_coeff)))
        #   exit()

        if calc == "lowdin":
            # Manually obtaining Lowdin's transformation matrix
            L, X = np.linalg.eigh(mol.intor("int1e_ovlp"))
            L = np.diag(L)
            eig_L = np.sqrt(np.linalg.inv(L))
            U = np.linalg.multi_dot((X, eig_L, X.T))

            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, U.T, eta[i]))
                SCR = np.dot(SCR, SCR.T) * np.outer(np.sqrt(N), np.sqrt(N))
                Smo.append(SCR)

        # Special case IAO
        elif calc == "iao" or calc == "nao" or calc == "meta_lowdin":
            raise NameError(f"{calc.upper()} not available for MCSCF calculations")

        # Special case plain Mulliken
        elif calc == "mulliken":
            eta = [np.zeros((mol.nao, mol.nao)) for i in range(mol.natm)]
            for i in range(mol.natm):
                start = mol.aoslice_by_atom()[i, -2]
                end = mol.aoslice_by_atom()[i, -1]
                eta[i][start:end, start:end] = np.eye(end - start)

            for i in range(mol.natm):
                SCR = np.linalg.multi_dot((occ_coeff.T, S, eta[i], occ_coeff))
                SCR = SCR * np.outer(np.sqrt(N), np.sqrt(N))
                Smo.append(SCR)

        else:
            raise NameError("Hilbert-space scheme not available")

        return Smo


def nao(mol, mf, s=None, restore=True):
    import sys
    from functools import reduce, lru_cache
    import numpy
    import scipy.linalg
    from pyscf import lib
    from pyscf import scf
    from pyscf.gto import mole
    from pyscf.lo import orth
    from pyscf.lib import logger
    from pyscf.data import elements
    from pyscf import __config__

    global AOSHELL
    AOSHELL = getattr(__config__, "lo_nao_AOSHELL", None)

    if AOSHELL is None:
        AOSHELL = list(zip(elements.N_CORE_SHELLS, elements.N_CORE_VALENCE_SHELLS))
    if s is None:
        if getattr(mol, "pbc_intor", None):  # whether mol object is a cell
            s = mol.pbc_intor("int1e_ovlp", hermi=1)
        else:
            s = mol.intor_symmetric("int1e_ovlp")
            dm = mf.make_rdm1()
    if isinstance(mf, (scf.uhf.UHF, scf.rohf.ROHF)):
        dm = dm[0] + dm[1]

    p = reduce(numpy.dot, (s, dm, s))
    pre_occ, pre_nao = _prenao_sub(mol, p, s)
    cnao = _nao_sub(mol, pre_occ, pre_nao)
    if restore:
        if mol.cart:
            # The atomic natural character for Cartesian basis is not clearly
            # defined. Skip restore.
            return cnao

        # restore natural character
        p_nao = reduce(numpy.dot, (cnao.T, p, cnao))
        s_nao = numpy.eye(p_nao.shape[0])
        cnao = numpy.dot(cnao, _prenao_sub(mol, p_nao, s_nao)[1])

        return cnao


def _prenao_sub(mol, p, s):
    import sys
    from functools import reduce, lru_cache
    import numpy
    import scipy.linalg
    from pyscf import lib
    from pyscf import scf
    from pyscf.gto import mole
    from pyscf.lo import orth
    from pyscf.lib import logger
    from pyscf.data import elements
    from pyscf import __config__

    ao_loc = mol.ao_loc_nr()
    nao = ao_loc[-1]
    occ = numpy.zeros(nao)
    cao = numpy.zeros((nao, nao))

    bas_ang = mol._bas[:, mole.ANG_OF]
    for ia, (b0, b1, p0, p1) in enumerate(mol.aoslice_by_atom(ao_loc)):
        l_max = bas_ang[b0:b1].max()
        for l in range(l_max + 1):
            idx = []
            for ib in numpy.where(bas_ang[b0:b1] == l)[0]:
                idx.append(numpy.arange(ao_loc[b0 + ib], ao_loc[b0 + ib + 1]))
            idx = numpy.hstack(idx)
            if idx.size < 1:
                continue

            if mol.cart:
                degen = (l + 1) * (l + 2) // 2
                p_frag = _cart_average_mat(p, l, idx)
                s_frag = _cart_average_mat(s, l, idx)
            else:
                degen = l * 2 + 1
                p_frag = _sph_average_mat(p, l, idx)
                s_frag = _sph_average_mat(s, l, idx)
            e, v = scipy.linalg.eigh(p_frag, s_frag)
            e = e[::-1]
            v = v[:, ::-1]

            idx = idx.reshape(-1, degen)
            for k in range(degen):
                ilst = idx[:, k]
                occ[ilst] = e
                for i, i0 in enumerate(ilst):
                    cao[i0, ilst] = v[i]
    return occ, cao


def _nao_sub(mol, pre_occ, pre_nao, s=None):
    from pyscf import lib
    from pyscf.lo import orth
    import numpy

    if s is None:
        if getattr(mol, "pbc_intor", None):  # whether mol object is a cell
            s = mol.pbc_intor("int1e_ovlp", hermi=1)
        else:
            s = mol.intor_symmetric("int1e_ovlp")
    core_lst, val_lst, rydbg_lst = _core_val_ryd_list(mol)
    nao = mol.nao_nr()
    pre_nao = pre_nao.astype(s.dtype)
    cnao = numpy.empty((nao, nao), dtype=s.dtype)

    if core_lst:
        c = pre_nao[:, core_lst].copy()
        s1 = reduce(lib.dot, (c.conj().T, s, c))
        cnao[:, core_lst] = c1 = lib.dot(c, orth.lowdin(s1))
        c = pre_nao[:, val_lst].copy()
        c -= reduce(lib.dot, (c1, c1.conj().T, s, c))
    else:
        c = pre_nao[:, val_lst]
    if val_lst:
        s1 = reduce(lib.dot, (c.conj().T, s, c))
        wt = pre_occ[val_lst]
        cnao[:, val_lst] = lib.dot(c, orth.weight_orth(s1, wt))

    if rydbg_lst:
        cvlst = core_lst + val_lst
        c1 = cnao[:, cvlst].copy()
        c = pre_nao[:, rydbg_lst].copy()
        c -= reduce(lib.dot, (c1, c1.conj().T, s, c))
        s1 = reduce(lib.dot, (c.conj().T, s, c))
        cnao[:, rydbg_lst] = lib.dot(c, orth.lowdin(s1))
    snorm = numpy.linalg.norm(
        reduce(lib.dot, (cnao.conj().T, s, cnao)) - numpy.eye(nao)
    )

    if snorm > 1e-9:
        lib.logger.warn(mol, "Weak orthogonality for localized orbitals %s", snorm)

    return cnao


def _core_val_ryd_list(mol):
    from pyscf.gto.ecp import core_configuration
    from pyscf.gto import mole
    import numpy

    count = numpy.zeros((mol.natm, 9), dtype=int)
    core_lst = []
    val_lst = []
    rydbg_lst = []
    k = 0
    for ib in range(mol.nbas):
        ia = mol.bas_atom(ib)
        # Avoid calling mol.atom_charge because we should include ECP core electrons here
        nuc = mole.charge(mol.atom_symbol(ia))
        l = mol.bas_angular(ib)
        nc = mol.bas_nctr(ib)
        nelec_ecp = mol.atom_nelec_core(ia)
        ecpcore = core_configuration(nelec_ecp, atom_symbol=mol.atom_pure_symbol(ia))
        coreshell = [int(x) for x in AOSHELL[nuc][0][::2]]
        cvshell = [int(x) for x in AOSHELL[nuc][1][::2]]
        if mol.cart:
            deg = (l + 1) * (l + 2) // 2
        else:
            deg = 2 * l + 1

        for n in range(nc):
            if l > 3:
                rydbg_lst.extend(range(k, k + deg))
            elif ecpcore[l] + count[ia, l] + n < coreshell[l]:
                core_lst.extend(range(k, k + deg))
            elif ecpcore[l] + count[ia, l] + n < cvshell[l]:
                val_lst.extend(range(k, k + deg))
            else:
                rydbg_lst.extend(range(k, k + deg))
            k = k + deg
        count[ia, l] += nc
    return core_lst, val_lst, rydbg_lst


@lru_cache(10)
def _cart_averge_wt(l):
    import numpy

    """Weight matrix for spherical symmetry averaging in Cartesian GTOs"""
    c = mole.cart2sph(l, normalized="sp")
    return numpy.einsum("pi,qi->pq", c, c)


def _cart_average_mat(mat, l, lst):
    import numpy

    degen = (l + 1) * (l + 2) // 2
    nshl = len(lst) // degen
    submat = mat[lst[:, None], lst].reshape(nshl, degen, nshl, degen)
    wt = _cart_averge_wt(l)
    return numpy.einsum("imjn,mn->ij", submat, wt) / (2 * l + 1)


def _sph_average_mat(mat, l, lst):
    import numpy

    degen = 2 * l + 1
    nshl = len(lst) // degen
    submat = mat[lst[:, None], lst].reshape(nshl, degen, nshl, degen)
    return numpy.einsum("imjm->ij", submat) / (2 * l + 1)


########### WRITING THE INPUT FOR THE ESI-3D CODE FROM THE AOMS ###########


def write_int(mol, mf, molname, Smo, ring=None, calc=None):
    import os

    if (
        mf.__class__.__name__ == "UHF"
        or mf.__class__.__name__ == "UKS"
        or mf.__class__.__name__ == "SymAdaptedUHF"
        or mf.__class__.__name__ == "SymAdaptedUKS"
    ):
        wf = "unrest"

    elif (
        mf.__class__.__name__ == "RHF"
        or mf.__class__.__name__ == "RKS"
        or mf.__class__.__name__ == "SymAdaptedRHF"
        or mf.__class__.__name__ == "SymAdaptedRKS"
    ):
        wf = "rest"

    else:
        wf = "no"
    # Obtaining information for the files

    symbols = [mol.atom_symbol(i) for i in range(mol.natm)]
    atom_numbers = [i + 1 for i in range(mol.natm)]
    charge = mol.atom_charges()
    if wf == "unrest":
        nocc_alpha = mf.mo_occ[0].astype(int)
        nocc_beta = mf.mo_occ[1].astype(int)
        occ_coeff_beta = mf.mo_coeff[0][:, : nocc_beta.sum()]
        nalpha = [(charge + np.trace(aom_alpha)) / 2 for aom_alpha in Smo[0]]
        nbeta = [(charge + np.trace(aom_beta)) / 2 for aom_beta in Smo[1]]

        Smos = []
        fill = np.zeros((nocc_beta.sum(), nocc_alpha.sum()))
        for i in range(mol.natm):
            left = np.vstack((Smo[0][i], fill))
            right = np.vstack((fill.T, Smo[1][i]))
            matrix = np.hstack((left, right))
            Smos.append(matrix)

    else:
        nalpha = nbeta = [(charge + np.trace(aom)) / 2 for aom in Smo]

    # Creating a new directory for the calculation

    if calc == "mulliken":
        shortcalc = "mul"
    elif calc == "lowdin":
        shortcalc = "low"
    elif calc == "meta_lowdin":
        shortcalc = "metalow"
    elif calc == "nao":
        shortcalc = "nao"
    elif calc == "iao":
        shortcalc = "iao"
    else:
        raise NameError("Hilbert-space scheme not available")

    new_dir_name = molname + "_" + shortcalc
    titles = [
        symbols[i] + str(atom_numbers[i]) + shortcalc for i in range(mol.natm)
    ]  # Setting the title of the files
    new_dir_path = os.path.join(os.getcwd(), new_dir_name)
    os.makedirs(new_dir_path, exist_ok=True)

    # Creating and writing the atomic .int files

    for i, item in enumerate(titles):
        with open(os.path.join(new_dir_path, item + ".int"), "w+") as f:
            f.write(" Created by ESIpy\n")
            if calc == "mulliken":
                f.write(" Using Mulliken atomic definition\n")
            elif calc == "lowdin":
                f.write(" Using Lowdin atomic definition\n")
            elif calc == "meta_lowdin":
                f.write(" Using Meta-Lowdin atomic definition\n")
            elif calc == "nao":
                f.write(" Using NAO atomic definition\n")
            elif calc == "iao":
                f.write(" Using IAO atomic definition\n")
            f.write(" Single-determinant wave function\n")
            if wf == "unrest" or wf == "rest":
                f.write(
                    " Molecular SCF ENERGY (AU)  =       {:.11f}\n\n".format(
                        mf.energy_tot()
                    )
                )
            else:
                f.write(" Molecular SCF ENERGY (AU)  =       \n\n")
            f.write(" INTEGRATION IS OVER ATOM  {}    {}\n".format(symbols[i], i + 1))
            f.write(" RESULTS OF THE INTEGRATION\n")
            if wf == "unrest":
                f.write(
                    "              N   {:.14E}    NET CHARGE {:.14E}\n".format(1, 1)
                )
            else:
                f.write(
                    "              N   {:.14E}    NET CHARGE {:.14E}\n".format(
                        2 * np.trace(Smo[i]),
                        round(charge[i] - 2 * np.trace(Smo[i]), 14),
                    )
                )
            f.write("              G\n")
            f.write(
                "              K   1.00000000000000E+01        E(ATOM)  1.00000000000000E+00\n"
            )
            f.write("              L   1.00000000000000E+01\n\n")

            if wf == "unrest":
                f.write("\n The Atomic Overlap Matrix:\n\nUnrestricted\n\n")
                f.write(
                    "\n".join(
                        [
                            "  ".join(
                                [
                                    "{:.16E}".format(Smos[i][j][k]) if j >= k else ""
                                    for k in range(len(Smos[i][j]))
                                ]
                            )
                            for j in range(len(Smos[i]))
                        ]
                    )
                    + "\n"
                )

            else:
                f.write(
                    "\n          The Atomic Overlap Matrix\n\nRestricted Closed-Shell Wavefunction\n\n  "
                )
                if calc == "mulliken":
                    f.write(
                        "  \n".join(
                            [
                                "  ".join(["{:.16E}".format(num, 16) for num in row])
                                for row in Smo[i]
                            ]
                        )
                        + "\n"
                    )
                else:
                    f.write(
                        "\n".join(
                            [
                                "  ".join(
                                    [
                                        "{:.16E}".format(Smo[i][j][k], 16)
                                        if j >= k
                                        else ""
                                        for k in range(len(Smo[i][j]))
                                    ]
                                )
                                for j in range(len(Smo[i]))
                            ]
                        )
                        + "\n"
                    )
            f.write(
                "\n                     ALPHA ELECTRONS (NA) {:E}\n".format(
                    nalpha[i][0], 14
                )
            )
            f.write(
                "                      BETA ELECTRONS (NB) {:E}\n\n".format(
                    nbeta[i][0], 14
                )
            )
            f.write(" NORMAL TERMINATION OF PROAIMV")
            f.close()

    # Writing the file containing the title of the atomic .int files

    with open(os.path.join(new_dir_path, molname + shortcalc + ".files"), "w") as f:
        for i in titles:
            f.write(i + ".int\n")
        f.close()
    # Creating the input for the ESI-3D code

    filename = os.path.join(new_dir_path, molname + ".bad")
    with open(filename, "w") as f:
        f.write("$TITLE\n")
        f.write(molname + "\n")
        f.write("$TYPE\n")
        if wf == "unrest":
            f.write("uhf\n{}\n".format(mol.nelec[0] + 1))
        else:
            f.write("hf\n")
        # f.write("$NOMCI\n")
        # f.write("$MCIALG\n1\n")
        f.write("$RING\n")
        if ring is not None:
            if isinstance(ring[0], int):  # If only one ring is specified
                f.write("1\n{}\n".format(len(ring)))
                f.write(" ".join(str(value) for value in ring))
                f.write("\n")
            else:
                f.write(
                    "{}\n".format(len(ring))
                )  # If two or more rings are specified as a list of lists
                for sublist in ring:
                    f.write(str(len(sublist)) + "\n")
                    f.write(" ".join(str(value) for value in sublist))
                    f.write("\n")
        else:
            f.write("\n")  # No ring specified, write it manually
        f.write("$ATOMS\n")
        f.write(str(mol.natm) + "\n")
        for title in titles:
            f.write(title + ".int\n")
        f.write("$BASIS\n")
        if wf == "unrest":
            f.write(str(int(np.shape(Smo[0])[1]) + int(np.shape(Smo[1])[1])) + "\n")
        elif wf == "unrest":
            f.write(str(int(np.shape(Smo)[1])) + "\n")
        else:
            f.write(str(np.shape(Smo)[1]) + "\n")
        f.write("$AV1245\n")
        f.write("$FULLOUT\n")
        if calc == "mulliken":
            f.write("$MULLIKEN\n")
