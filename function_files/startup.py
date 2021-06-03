'''
Set up instances for the various pieces of equipment in the network.  Ping all
networked devices to ensure we have communication before we begin running our
program.

Functions
---------

    startup()

'''

# devices = {
#     'MFC_C2H4':'101',
#     'MFC_Ar':'102',
#     'MFC_He':'103',
#     'MFC_H2':'104',
#     'Furnace':'150'
# }

def startup():
    MFC_C2H4 = MFC(101)
    MFC_Ar = MFC(102)
    MFC_He = MFC(103)
    MFC_H2 = MFC(104)
    furnace = furnace(150)

    a = MFC_C2H4.QueryOpMode()
    b = MFC_Ar.QueryOpMode()
    c = MFC_He.QueryOpMode()
    d = MFC_H2.QueryOpMode()
    e = furnace.ReportStatus()

    if a and b and c and d and e:
        print('All devices online.')

    # for device in devices:
    #     operating_mode = MFC_command(devices[device],'query_operating_mode')

if __name__ == '__main__':
    import sys
    sys.path.append('.')
    from function_files.equipment import *
    startup()