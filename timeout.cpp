#define _WIN32_WINNT 0x0600
#include <iostream>
#include <windows.h>
#include <winnt.h> 
#include <initguid.h>
//initguidҪ��powrprofǰ���� 
#include <powrprof.h>

#pragma comment(lib, "PowrProf.lib")
using namespace std;

void set_sleep_never(GUID GUID_BALANCED_POWER_POLICY) {
    SYSTEM_POWER_POLICY policy;
    ZeroMemory(&policy, sizeof(policy));
    if (PowerWriteACValueIndex(NULL, &GUID_BALANCED_POWER_POLICY, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, 0) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_BALANCED_POWER_POLICY, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, 0) == ERROR_SUCCESS) {
        std::cout << "˯��ʱ��������Ϊ������" << std::endl;
    } else {
        std::cout << "����˯��ʱ��ʧ�ܡ�" << std::endl;
    }
}



// ���� GUID_VIDEO_TIMEOUT (��Ļ�رճ�ʱ)
DEFINE_GUID(GUID_VIDEO_TIMEOUT, 
0x3c0bc021, 0xc8a8, 0x4e07, 0xa9, 0x73, 0x6b, 0x14, 0xcb, 0xcb, 0x2b, 0x7e);

// ���� GUID_VIDEO_SUBGROUP
DEFINE_GUID(GUID_VIDEO_SUBGROUP, 
0x7516b95f, 0xf776, 0x4464, 0x8c, 0x53, 0x06, 0x16, 0x7f, 0x40, 0xcc, 0x99);

// ���� GUID_SLEEP_SUBGROUP��˯���������飩
DEFINE_GUID(GUID_SLEEP_SUBGROUP, 
0x238c9fa8, 0x0aad, 0x41ed, 0x83, 0xf4, 0x97, 0xbe, 0x24, 0x2c, 0x8f, 0x20);

// ���� GUID_STANDBY_TIMEOUT��������ʱ���ã�
DEFINE_GUID(GUID_STANDBY_TIMEOUT, 
0x29f6c1db, 0x86da, 0x48c5, 0x9f, 0xdb, 0xf2, 0xb6, 0x7b, 0x1f, 0x44, 0xda);

//ƽ��ƻ� (Balanced):
//381b4222-f694-41f0-9685-ff5bb260df2e
GUID GUID_BALANCED = { 0x381b4222, 0xf694, 0x41f0, { 0x96, 0x85, 0xff, 0x5b, 0xb2, 0x60, 0xdf, 0x2e } };

//�����ܼƻ� (High Performance):
//8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
GUID GUID_HIGH_PERFORMANCE = { 0x8c5e7fda, 0xe8bf, 0x4a96, { 0x9a, 0x85, 0xa6, 0xe2, 0x3a, 0x8c, 0x63, 0x5c } };

//���ܼƻ� (Power Saver):
//a1841308-3541-4fab-bc81-f71556f20b4a
GUID GUID_POWER_SAVER = { 0xa1841308, 0x3541, 0x4fab, { 0xbc, 0x81, 0xf7, 0x15, 0x56, 0xf2, 0x0b, 0x4a } };
void set_screen_timeout_never(GUID GUID_TARGET) {
    // ������Ļ�ر�ʱ��Ϊ������AC ģʽ�� DC ģʽ�ֱ����ã�
    if (PowerWriteACValueIndex(
            NULL,
            &GUID_TARGET,    // ƽ���Դ�ƻ�
            &GUID_VIDEO_SUBGROUP,          // ��Ƶ��������
            &GUID_VIDEO_TIMEOUT,           // ��Ļ��ʱ����
            0) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(
            NULL,
            &GUID_TARGET,
            &GUID_VIDEO_SUBGROUP,
            &GUID_VIDEO_TIMEOUT,
            0) == ERROR_SUCCESS) {
        // ������Ӧ�õ�ϵͳ
        if (PowerSetActiveScheme(NULL, &GUID_TARGET) == ERROR_SUCCESS) {
            std::cout << "��Ļ�ر�ʱ��������Ϊ������" << std::endl;
        } else {
            std::cout << "Ӧ�õ�Դ�ƻ�ʧ�ܡ�" << std::endl;
        }
    } else {
        std::cout << "������Ļ�ر�ʱ��ʧ�ܡ�" << std::endl;
    }
}

void set_lid_close_action() {
    HKEY hKey;
    LPCSTR path = "SYSTEM\\CurrentControlSet\\Control\\Power";
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, path, 0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        DWORD data_sleep = 0x00000001; // �޲��� 

        // ���ý�ͨ��Դģʽ�ĺϸǲ���
        if (RegSetValueExA(hKey, "LidCloseAction", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
            std::cout << "���ϱʼǱ����ӣ���ͨ��Դģʽ��������Ϊ�ޡ�" << std::endl;
        } else {
            std::cout << "���úϸǲ�������ͨ��Դģʽ��ʧ�ܡ�" << std::endl;
        }

        // ���õ�ع���ģʽ�ĺϸǲ���
        if (RegSetValueExA(hKey, "LidCloseAction_DC", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
            std::cout << "���ϱʼǱ����ӣ���ع���ģʽ��������Ϊ�ޡ�" << std::endl;
        } else {
            std::cout << "���úϸǲ�������ع���ģʽ��ʧ�ܡ�" << std::endl;
        }

        RegCloseKey(hKey);
    } else {
        std::cout << "�޷���ע���" << std::endl;
    }
}
int main() {
    set_sleep_never(GUID_POWER_SAVER);
    set_sleep_never(GUID_BALANCED);
    set_screen_timeout_never(GUID_POWER_SAVER);
    set_screen_timeout_never(GUID_BALANCED);
    set_lid_close_action();
    return 0;
}

