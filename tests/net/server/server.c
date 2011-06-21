
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#define BUFSIZE 2


int main(int argc, char *argv[])
{  
    sockaddr_in sockName;                   // "Jm�no" soketu
    sockaddr_in clientInfo;                 // Informace o p�ipojen�m klientovi
    int Socket;                             // Soket
    int port;                               // ��slo portu
    char buf[BUFSIZE];                      // P�ij�mac� buffer
    int size;                               // Po�et p�ijat�ch a odeslan�ch byt�
    socklen_t addrlen;                      // Velikost adresy vzd�len�ho po��ta�e
    int count = 0;                          // Po�et p�ipojen�

    if (argc != 2)
    {
        fprintf(stderr, "Pouziti:\n\t%s port\n", argv[0]);
        return 1;
    }
    port = atoi(argv[1]);
    // Vytvo��me soket - viz minul� d�l
    if ((Socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        perror("socket: ");
        return 1;
    }
    // Zapln�me strukturu sockaddr_in
    // 1) Rodina protokol�
    sockName.sin_family = AF_INET;
    // 2) ��slo portu, na kter�m �ek�me
    sockName.sin_port = htons(port);
    // 3) Nastaven� IP adresy lok�ln� s�ov� karty, p�es kterou je mo�no se
    //    p�ipojit. Nastav�me mo�nost p�ipojit se odkudkoliv. 
    sockName.sin_addr.s_addr = INADDR_ANY;
    // p�i�ad�me soketu jm�no
    if (bind(Socket, (sockaddr *)&sockName, sizeof(sockName)) == -1)
    {
        perror("bind: ");
        return 1;
    }
       
    char c = 'A';
    while (1)
    {
        char temp[2];
    	sprintf(temp,"%c", c);
        
        addrlen = sizeof(clientInfo);
        if ((size = recvfrom(Socket, buf, BUFSIZE - 1, 0, (sockaddr *)&clientInfo, &addrlen)) == -1)
        {
            perror("recvfrom: ");
        }
        else
        {
            buf[size] = '\0';
            fprintf(stdout, "recv %s\n", buf);
            fflush(stdout);
        }

        if (sendto(Socket, temp, strlen(temp), 0, (sockaddr *)&clientInfo, addrlen) == -1)
        {
                perror("sendto: ");
        }
        else
        {
            fprintf(stdout, "send %c\n", c);
            fflush(stdout);
        }
        
        if (c == 'Z')
            c = 'A';
        else
            c++;
    }

   

    close(Socket);    
    return 0;
}
