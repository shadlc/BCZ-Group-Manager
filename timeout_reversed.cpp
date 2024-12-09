#define _WIN32_WINNT 0x0600
#include <iostream>
#include <windows.h>
#include <winnt.h> 
#include <initguid.h>
#include <powrprof.h>

#pragma comment(lib, "PowrProf.lib")
using namespace std;

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

// ƽ��ƻ� (Balanced)
GUID GUID_BALANCED = { 0x381b4222, 0xf694, 0x41f0, { 0x96, 0x85, 0xff, 0x5b, 0xb2, 0x60, 0xdf, 0x2e } };

void set_screen_timeout_3min(GUID GUID_TARGET) {
    // ������Ļ�ر�ʱ��Ϊ3���ӣ�AC ģʽ�� DC ģʽ�ֱ����ã�
    DWORD timeout = 180; // 3����
    if (PowerWriteACValueIndex(NULL, &GUID_TARGET, &GUID_VIDEO_SUBGROUP, &GUID_VIDEO_TIMEOUT, timeout) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_TARGET, &GUID_VIDEO_SUBGROUP, &GUID_VIDEO_TIMEOUT, timeout) == ERROR_SUCCESS) {
        if (PowerSetActiveScheme(NULL, &GUID_TARGET) == ERROR_SUCCESS) {
            std::cout << "��Ļ�ر�ʱ��������Ϊ3���ӡ�" << std::endl;
        } else {
            std::cout << "Ӧ�õ�Դ�ƻ�ʧ�ܡ�" << std::endl;
        }
    } else {
        std::cout << "������Ļ�ر�ʱ��ʧ�ܡ�" << std::endl;
    }
}

void set_sleep_3min(GUID GUID_TARGET) {
    DWORD timeout = 180; // 3����
    if (PowerWriteACValueIndex(NULL, &GUID_TARGET, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, timeout) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_TARGET, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, timeout) == ERROR_SUCCESS) {
        std::cout << "˯��ʱ��������Ϊ3���ӡ�" << std::endl;
    } else {
        std::cout << "����˯��ʱ��ʧ�ܡ�" << std::endl;
    }
}

void set_lid_close_sleep() {
    HKEY hKey;
    LPCSTR path = "SYSTEM\\CurrentControlSet\\Control\\Power";
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, path, 0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        DWORD data_sleep = 0x00000002; // ����Ϊ˯��

        // ���ý�ͨ��Դģʽ�ĺϸǲ���
        if (RegSetValueExA(hKey, "LidCloseAction", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
            std::cout << "���ϱʼǱ����ӣ���ͨ��Դģʽ��������Ϊ˯�ߡ�" << std::endl;
        } else {
            std::cout << "���úϸǲ�������ͨ��Դģʽ��ʧ�ܡ�" << std::endl;
        }

        // ���õ�ع���ģʽ�ĺϸǲ���
        if (RegSetValueExA(hKey, "LidCloseAction_DC", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
            std::cout << "���ϱʼǱ����ӣ���ع���ģʽ��������Ϊ˯�ߡ�" << std::endl;
        } else {
            std::cout << "���úϸǲ�������ع���ģʽ��ʧ�ܡ�" << std::endl;
        }

        RegCloseKey(hKey);
    } else {
        std::cout << "�޷���ע���" << std::endl;
    }
}

int main() {
    set_sleep_3min(GUID_BALANCED);
    set_screen_timeout_3min(GUID_BALANCED);
    set_lid_close_sleep();
    return 0;
}

